LOTS = {
    "LOT-4821": {"component":"Power control module", "affected":1240,"shipped":318,"on_hand":922,"customers":{"Atlas Robotics":79,"Nova Industrial":79,"Orion Motors":80,"Vela Mobility":80},"plants":{"Austin":414,"Detroit":413,"Reno":413},"evidence":["ENG-044","QIR-101","SCAR-019"]},
    "LOT-7103": {"component":"Servo controller", "affected":460,"shipped":120,"on_hand":340,"customers":{"Orion Motors":70,"Atlas Robotics":50},"plants":{"Austin":240,"Reno":220},"evidence":["ENG-071","QIR-203"]},
    "LOT-9902": {"component":"Thermal sensor assembly", "affected":210,"shipped":40,"on_hand":170,"customers":{"Nova Industrial":40},"plants":{"Detroit":210},"evidence":["QIR-302"]},
}
DOCUMENTS = {
    "ENG-044":{"title":"Engineering containment guidance","text":"Containment proposal: hold on hand units from the suspect supplier lot. Escalate shipped serials to quality leadership for customer notification decision. Do not initiate customer communications without approval."},
    "QIR-101":{"title":"Thermal cycling inspection LOT-4821","text":"Inspection found intermittent shutdown after 600 thermal cycles in 7 of 80 sampled power modules. Confirm lot genealogy and quarantine remaining inventory pending engineering review."},
    "SCAR-019":{"title":"Supplier corrective action Northstar","text":"Supplier investigation indicates possible solder joint fatigue in the power stage. Root cause not confirmed. Request cross section analysis and updated process capability records."},
    "ENG-071":{"title":"Servo controller containment","text":"Review affected controllers for calibration drift. Quarantine available inventory until validation is complete."},
    "QIR-203":{"title":"Servo controller inspection","text":"Six of 50 sampled controllers showed calibration drift after repeated duty cycles."},
    "QIR-302":{"title":"Thermal sensor inspection","text":"Two of 40 sampled sensors reported temperature deviations. Engineering validation is pending."},
}
