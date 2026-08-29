from dotenv import load_dotenv
load_dotenv()
from app.core.crew_runner import run_crew
import litellm

_orig = litellm.completion
def my_completion(*args, **kwargs):
    print(">>> LITELLM COMPLETION KWARGS:", kwargs)
    try:
        return _orig(*args, **kwargs)
    except Exception as e:
        print(">>> LITELLM ERROR:", type(e), e)
        raise e

litellm.completion = my_completion

for chunk in run_crew("God", "Test message"):
    pass
