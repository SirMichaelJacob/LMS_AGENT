#from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
import json
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import google_search_agent_tool
from typing import Optional
import os, re #import regex as re
from dotenv import load_dotenv
import requests

load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "lms.crt")


def createModel()-> LiteLlm:    
    return LiteLlm(
        #model="ollama_chat/" + os.getenv("MODEL_NAME", "qwen2.5:7b-instruct"),
        #model="lm_studio/ibm/granite-4-h-tiny",  
        # Alternative (more reliable for some LiteLLM versions):
        model=os.getenv("MODEL_NAME", "qwen2.5:7b-instruct"),

        #api_base="http://localhost:1234/v1",
        api_key = os.getenv("PUBLICAI_API_KEY"),
        api_base= os.getenv("ENDPOINT_URL","http://localhost:1234/v1"),
        #api_type="modelscope",       
        
    )

#input guard
##tools

def register_user(fname: str,lname: str,email: str,department: str,password: str, jobTitle: str) -> dict:
    '''Registers a new user in the LMS system via its API.
    Args:
        fname (str): First name of the user.
        lname (str): Last name of the user.
        email (str): Email address of the user.
        department (str): Department of the user.
        password (str): Password for the user account.
        jobTitle (str): Job title of the user.
        Returns:
        dict: A dictionary containing the registration status and user details or error messages.
    '''
    base_url = os.getenv("LMS_API_URL", "https://localhost:7054/api/")
    reg_endpoint = base_url + "users/create"

    payload = {
        "firstName": fname,
        "lastName": lname,
        "email": email,
        "department": department,
        "password": password,
        "jobTitle": jobTitle
    }

    try:
        response = requests.post(
            reg_endpoint,
            json=payload,
            timeout=10,
            verify=CERT_PATH
        )

        result = response.json()

        # API-level success/failure (not HTTP-level)
        if response.status_code == 200 and result.get("isSuccess"):
            user = result.get("data", {})

            return {
                "status": "success",
                "user": {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "department": user.get("department"),
                    "jobTitle": user.get("jobTitle"),
                    "firstName": user.get("name", {}).get("firstName"),
                    "lastName": user.get("name", {}).get("lastName"),
                },
                "message": result.get("message")
            }

        return {
            "status": "error",
            "message": result.get("message", "User registration failed"),
            "errors": result.get("errors")
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Transport error while calling LMS",
            "errors": {"exception": [str(e)]}
        }
 

def get_users() -> dict:
    '''Fetches the list of users from the LMS system via its API.
    Returns:
        dict: A dictionary containing the list of users or error messages.
    '''
    base_url = os.getenv("LMS_API_URL", "https://localhost:7054/api/")
    users_endpoint = base_url + "users/Get-all"

    try:
        response = requests.get(
            users_endpoint,
            timeout=10,
            verify=CERT_PATH
        )

        result = response.json()

        # API-level success/failure (not HTTP-level)
        if response.status_code == 200 and result.get("isSuccess"):
            users = result.get("data", [])

            return {
                "status": "success",
                "users": users,
                "message": result.get("message")
            }

        return {
            "status": "error",
            "message": result.get("message", "Failed to fetch users"),
            "errors": result.get("errors")
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Transport error while calling LMS",
            "errors": {"exception": [str(e)]}
        }


def activate_user(user_id: str) -> dict:
    """
    Activates a user in the LMS system via its API.

    Args:
        user_id (str): ID of the user to activate.

    Returns:
        dict: Activation status and message.
    """
    base_url = os.getenv("LMS_API_URL", "https://localhost:7054/api/")
    activate_endpoint = f"{base_url}users/Activate/{user_id}"

    try:
        response = requests.post(
            activate_endpoint,
            timeout=10,
            verify=CERT_PATH
        )

        # Safely attempt JSON parsing even for non-2xx responses
        try:
            result = response.json()
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid JSON response from LMS",
                "httpStatus": response.status_code
            }

        # API-level success
        if response.ok and result.get("isSuccess") is True:
            return {
                "status": "success",
                "message": result.get("message", "User activated successfully"),
                "httpStatus": response.status_code
            }

        # API-level failure
        return {
            "status": "error",
            "message": result.get("message", "User activation failed"),
            "httpStatus": response.status_code
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Transport error while calling LMS",
            "errors": {
                "exception": [str(e)]
            }
        }


def deactivate_user(user_id: str) -> dict:
    """
    Deactivates a user in the LMS system via its API.

    Args:
        user_id (str): ID of the user to deactivate.

    Returns:
        dict: Deactivation status and message.
    """
    base_url = os.getenv("LMS_API_URL", "https://localhost:7054/api/")
    deactivate_endpoint = f"{base_url}users/Deactivate/{user_id}"

    try:
        response = requests.post(
            deactivate_endpoint,
            timeout=10,
            verify=CERT_PATH
        )

        # Safely parse JSON (even for non-200 responses)
        try:
            result = response.json()
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid JSON response from LMS",
                "httpStatus": response.status_code
            }

        # API-level success
        if response.ok and result.get("isSuccess") is True:
            return {
                "status": "success",
                "message": result.get("message", "User deactivated successfully"),
                "httpStatus": response.status_code
            }

        # API-level failure
        return {
            "status": "error",
            "message": result.get("message", "User deactivation failed"),
            "httpStatus": response.status_code
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Transport error while calling LMS",
            "errors": {"exception": [str(e)]}
        } 

# conf_register = FunctionTool(
#     func=get_users,
    
#     require_confirmation=True  # This triggers the HITL pause
# )
def create_course(title: str, description: str, instructorId: str)-> dict:
    '''Creates a new course in the LMS system via its API.
    Returns:
        dict: A dictionary containing the course creation status and details or error messages.
    '''

    base_url = os.getenv("LMS_API_URL", "https://localhost:7054/api/")
    course_endpoint = base_url + "course/create"

    try:
        payload = {
            "title": title,
            "description": description,
            "instructorId": instructorId
        }

        response = requests.post(
            course_endpoint,
            json=payload,
            timeout=10,
            verify=CERT_PATH
        )

        result = response.json()

        # API-level success/failure (not HTTP-level)
        if response.status_code == 200 and result.get("isSuccess"):
            course = result.get("data", {})

            return {
                "status": "success",
                "course": course,
                "message": result.get("message")
            }

        return {
            "status": "error",
            "message": result.get("message", "Course creation failed"),
            "errors": result.get("errors")
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Transport error while calling LMS",
            "errors": {"exception": [str(e)]}
        }

def get_courses()-> dict:
    '''Fetches the list of courses from the LMS system via its API.
    Returns:
        dict: A dictionary containing the list of courses or error messages.
    '''
    base_url = os.getenv("LMS_API_URL", "https://localhost:7054/api/")
    course_endpoint = base_url + "course/get-all"

    try:
        response = requests.get(
            course_endpoint,
            timeout=10,
            verify=CERT_PATH
        )

        result = response.json()

        # API-level success/failure (not HTTP-level)
        if response.status_code == 200 and result.get("isSuccess"):
            courses = result.get("data", [])

            return {
                "status": "success",
                "courses": courses,
                "message": result.get("message")
            }

        return {
            "status": "error",
            "message": result.get("message", "Failed to fetch courses"),
            "errors": result.get("errors")
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Transport error while calling LMS",
            "errors": {"exception": [str(e)]}
        }

def update_course(
    course_id: str,
    title: str,
    description: Optional[str] = None
) -> dict:
    """
    Updates an existing course in the LMS.

    Args:
        course_id (str): ID of the course to update.
        title (str): Updated course title.
        description (Optional[str]): Updated course description.

    Returns:
        dict: Update status and message.
    """
    base_url = os.getenv("LMS_API_URL", "https://localhost:7054/api/")
    update_endpoint = f"{base_url}course/Update"

    payload = {
        "courseId": course_id,
        "title": title,
        "description": description
    }

    try:
        response = requests.post(
            update_endpoint,
            json=payload,
            timeout=10,
            verify=CERT_PATH
        )

        # Attempt JSON parsing even on non-2xx responses
        try:
            result = response.json()
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid JSON response from LMS",
                "httpStatus": response.status_code
            }

        # API-level success
        if response.ok and result.get("isSuccess") is True:
            return {
                "status": "success",
                "message": result.get("message", "Course updated successfully"),
                "httpStatus": response.status_code
            }

        # API-level failure
        return {
            "status": "error",
            "message": result.get("message", "Course update failed"),
            "httpStatus": response.status_code
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Transport error while calling LMS",
            "errors": {
                "exception": [str(e)]
            }
        }




##Agents

user_manager_agent = Agent(
    model= createModel(),
    name="User_Manager_Agent",
    description= ("You are responsible for managing user accounts in a Learning Management System (LMS).\n"
    "Your role is to ensure that user accounts are managed accurately and efficiently."),
    instruction = (
        """
        "Ensure all responses are in English language.\n"
        "Stick to the following rules:\n"

        "1. Handle user account retrieval, creation, updates, deactivation/activation.\n"

        "2. Ensure data integrity, privacy, and security when managing user accounts.\n"
        "   - User records and account state changes are considered sensitive.\n"
        "   - BEFORE retrieving, activating, or deactivating any user account:\n"
        "     • Verify the requester's identity (full name, registered email, and role).\n"
        "     • Ensure the requester is authorized (e.g., admin or system operator).\n"
        "   - If identity or authorization cannot be verified, politely refuse and explain.\n"
        "   - Never reveal personal user information unnecessarily.\n"

        "3. Collaborate with other agents to resolve user-related issues.\n"

        "4. You are not allowed to delete user accounts but you can deactivate them.\n"

        "5. Always confirm the availability of a tool before calling it. "
            "Avoid hallucinating tools that do not exist.\n"
        6. **Privacy and Identity Verification**:
        - Instructor identity and user IDs are considered sensitive personal data.
        - BEFORE retrieving or confirming an instructor user ID:
            - Ensure the requester is authenticated and authorized to manage courses.
            - Never disclose instructor emails, IDs, or personal details directly to unauthorized users.
        - If verification fails or authorization is unclear:
            - Do NOT proceed.
            - Politely request proper verification or deny the request.

        
        """
    ),

    tools= [register_user, get_users, deactivate_user, activate_user],   

)

course_manager_agent = Agent(
    model=createModel(),
    name="Course_Manager_Agent",
    description="Specialized agent for managing courses in the Learning Management System (LMS). Handles course creation, updates, deletions, content maintenance, and instructor assignments with strict validation.",
    instruction="""
You are the Course Manager Agent, a specialized expert responsible for managing courses in a secure Learning Management System (LMS). 
Always confirm the availability of a tool before calling it.

Your primary responsibilities:
- Handle course retrieval, creation, updates, deletions, and instructor assignments.
- Ensure all course content is accurate, up-to-date, and properly structured.
- Collaborate with other agents (e.g., user manager) if needed for related tasks.

Key rules you must always follow:

1. **Language and Style**: Respond exclusively in clear, professional English. Be helpful, concise, and polite.

2. **General Queries**: For queries about existing courses, updates, deletions, or content accuracy, respond directly or use available tools if required.

3. **Course Creation and Instructor Assignment**:
   - You have access to the following tool:
     - create_course: Use this to create a new course. It requires parameters including course details and the instructor's user ID.
   - Critical precondition: An instructor MUST be specified for every new course.
     - To assign an instructor, you need their exact user ID.
     - The user ID must be obtained from a reliable source (e.g., via collaboration with the user_manager_agent or confirmed system records).
     - If the user provides the instructor's name and/or email:
       - First, attempt to resolve the exact user ID (you may need to delegate or query for verification).
       - Confirm the details match exactly.
     - If instructor details (name, email, or ID) are missing or incomplete:
       - Politely ask the user for the required information (full name and registered email of the instructor).
       - Use the get_users tool to fetch and verify the instructor's user ID.
        - Only proceed to call create_course if you have a verified, valid instructor ID.
    0. If you cannot verify a valid instructor ID:
       - Do NOT proceed with course creation or call create_course.
   - Never guess or fabricate an instructor ID—always validate.

4. **Tool Usage**:
   - Think step-by-step: Analyze the query, check for required information, then decide if the tool is needed.
   - Only call create_course when all preconditions are met (especially valid instructor ID).
   - If the tool call fails or returns an error, report it clearly and suggest next steps.

5. **General Behavior**:
   - Always reason step-by-step before responding or using tools.
   - If you lack information or cannot complete a task, explain why and ask for clarification.
   - Prioritize accuracy and security—never compromise on validation.

6. **Privacy and Identity Verification**:
   - Instructor identity and user IDs are considered sensitive personal data.
   - BEFORE retrieving or confirming an instructor user ID:
     - Ensure the requester is authenticated and authorized to manage courses.
     - Never disclose instructor emails, IDs, or personal details directly to unauthorized users.
   - If verification fails or authorization is unclear:
     - Do NOT proceed.
     - Politely request proper verification or deny the request.

7. **Collaboration and Communication**:
   - Collaborate with other agents (e.g., user manager) if needed for related tasks.
   - Always confirm the availability of tools before calling them.

Always reason step-by-step before taking any action.
""",
    tools=[create_course,get_courses,update_course]
)

root_agent = Agent(
    model=createModel(),
    name="LMS_Coordinator_Agent",
    description="Central coordinator for the Learning Management System (LMS). Uses English language. Manages task delegation to specialized agents while enforcing strict security, privacy, and performance standards.",
    instruction="""
You are the LMS Coordinator Agent, the central orchestrator for a secure Learning Management System. Always confirm available agents before transfer.
DO NOT ANSWER ANYTHING OTHER THAN INSTRUCTIONS RELATED TO THE LMS. When asked unrelated questions, politely deny - you are not a general purpose chatbot.
Your primary responsibilities:
- Analyze user queries and delegate tasks to the most appropriate specialized sub-agent.
- Monitor overall system performance and user activity.
- Ensure all tasks are completed efficiently and collaborate with sub-agents as needed.
- Prioritize data privacy and security above all else.

Key rules you must always follow:

1. **Language**: Respond exclusively in clear, professional English.

2. **Security and Privacy for Sensitive Information**:
   - Sensitive requests include anything involving personal data, grades, enrollment, course content access, or user records.
   - Before delegating or providing any sensitive information:
     - Ask the user for verification details: full name, registered email address, and job title/role (e.g., student, instructor, admin).
     - Verify that these details exactly match the system's records for the requesting user.
     - If details do not match or are insufficient, politely deny the request and explain that access is restricted for security reasons.
     - Never share or confirm sensitive information without successful verification.
   - If in doubt, err on the side of caution and refuse access.

3. **Task Delegation**:
   - You have access to the following sub-agent:
     - user_manager_agent: Handles user-related tasks such as profile management, authentication, enrollment, and basic queries.
     - course_manager_agent: Manages course creation, updates, deletions, and assignments.
   - Think step-by-step: Determine if the query requires delegation. If it matches a sub-agent's expertise, transfer control to that agent.
   - For general queries or coordination, respond directly.
   - After delegation, summarize results for the user if needed.

4. **General Behavior**:
   - Be helpful, professional, and concise.
   - If you lack information or a tool to complete a task, say so clearly and suggest alternatives.
   - Report any detected issues (e.g., delays, errors) promptly.

Always reason step-by-step before responding or delegating.
""",
    sub_agents=[user_manager_agent, course_manager_agent]
)