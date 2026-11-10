from app.tools import run_tool
from app.retrieval import search
from app.enterprise_agent import fallback_plan

def test_tools():
    assert run_tool('lot_overview','LOT-4821','')['affected']==1240
    assert run_tool('propose_containment','LOT-4821','')['requires_approval']

def test_search():
    assert search('thermal cycling', 'LOT-4821')
    assert all('id' in x and 'score' in x for x in search('inspection','LOT-4821'))

def test_planning():
    assert 'customer_exposure' in fallback_plan('Which customers are exposed?')
    assert 'propose_containment' in fallback_plan('Prepare containment actions')
