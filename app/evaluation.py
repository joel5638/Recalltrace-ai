"""Offline regression checks for factual accuracy and safe tool routing."""
import asyncio,json
from .enterprise_agent import chat

CASES=[
 {"question":"How many units are affected in LOT-4821?","required":["1,240"],"forbidden":["not sure"]},
 {"question":"How many shipped units for LOT-4821?","required":["318"],"forbidden":[]},
 {"question":"What evidence supports LOT-4821?","required":["ENG-044"],"forbidden":[]},
]
async def evaluate():
    import uuid
    output=[]
    for case in CASES:
        result=await chat(str(uuid.uuid4()),case["question"])
        answer=result["answer"]
        passed=all(x.lower() in answer.lower() for x in case["required"]) and not any(x.lower() in answer.lower() for x in case["forbidden"])
        output.append({"question":case["question"],"passed":passed,"answer":answer})
    return {"passed":sum(x["passed"] for x in output),"total":len(output),"cases":output}
if __name__=="__main__":print(json.dumps(asyncio.run(evaluate()),indent=2))
