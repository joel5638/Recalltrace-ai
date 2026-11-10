"""Read-only business tools. Writes are always routed to human approval."""
from .data import LOTS
from .retrieval import search

TOOL_NAMES=('lot_overview','customer_exposure','plant_exposure','search_evidence','compare_lots','propose_containment')

def run_tool(name,lot,question):
    if name=='compare_lots':return {'lots':{k:{'affected':v['affected'],'shipped':v['shipped'],'on_hand':v['on_hand']} for k,v in LOTS.items()}}
    if lot not in LOTS:return {'error':'Unknown lot. Choose LOT-4821, LOT-7103 or LOT-9902.'}
    d=LOTS[lot]
    if name=='lot_overview':return {'lot':lot,'component':d['component'],'affected':d['affected'],'shipped':d['shipped'],'on_hand':d['on_hand']}
    if name=='customer_exposure':return {'lot':lot,'customers':d['customers'],'shipped':d['shipped']}
    if name=='plant_exposure':return {'lot':lot,'plants':d['plants']}
    if name=='search_evidence':return {'lot':lot,'documents':search(question,lot)}
    if name=='propose_containment':return {'lot':lot,'proposals':[f"Review inventory hold for {d['on_hand']} on hand units",f"Prepare shipped unit impact list for {d['shipped']} units",'Request supplier root cause and corrective action evidence'],'requires_approval':True}
    return {'error':'Tool not available'}
