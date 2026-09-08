def foo():
    raise ValueError("This value is invalid")


# try:
#     foo()
# # except Exception as e:
# #     raise RuntimeError(f"Something went wrong: {e}")
# except Exception as e:
#     raise ValueError("The Problem is: ", e)
#     # print("it has been raised")

print("hello")
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

load_dotenv()
S_Url, S_Key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")

supabase = create_client(S_Url, S_Key)

print(supabase.table("users").select("hashed_password").execute())
print(supabase.table("users").select("hashed_password").eq("email", "user@example.com").execute().data[0]["hashed_password"])

# .("email", "user@example.com")

print(type(uuid.uuid4()))