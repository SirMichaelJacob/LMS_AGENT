#from google.adk.agents.llm_agent import Agent

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os
from dotenv import load_dotenv
import requests

load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "lms.crt")

##Functions

def createModel()-> LiteLlm:    
    return LiteLlm(
        model = os.getenv("MODEL_NAME","ollama/gemma3:27b"),
        api_key = os.getenv("API_KEY")
    )

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

##Agents
user_manager_agent = Agent(
    model= createModel(),
    name="User_Manager_Agent",
    description= ("You are responsible for managing user accounts in a Learning Management System (LMS).\n"
    "Your role is to ensure that user accounts are managed accurately and efficiently."),
    instruction = ("Ensure all responses are in English language.\n Stick to the following rules:\n"
    "1. Handle user account retrieval, creation, updates, and deletions.\n"
    "2. Ensure data integrity and security when managing user accounts.\n"
    "3. Collaborate with other agents to resolve user-related issues.\n"),
    tools= [register_user, get_users]

)

root_agent = Agent(
    model=createModel(),
    name="LMS_Coordinator_Agent",
    description="Central coordinator for the Learning Management System (LMS). Uses English language. Manages task delegation to specialized agents while enforcing strict security, privacy, and performance standards.",
    instruction="""
You are the LMS Coordinator Agent, the central orchestrator for a secure Learning Management System.

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
   - Think step-by-step: Determine if the query requires delegation. If it matches a sub-agent's expertise, transfer control to that agent.
   - For general queries or coordination, respond directly.
   - After delegation, summarize results for the user if needed.

4. **General Behavior**:
   - Be helpful, professional, and concise.
   - If you lack information or a tool to complete a task, say so clearly and suggest alternatives.
   - Report any detected issues (e.g., delays, errors) promptly.

Always reason step-by-step before responding or delegating.
""",
    sub_agents=[user_manager_agent]
)

