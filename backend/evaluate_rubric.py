"""Small reproducible demo evaluation; not a benchmark or representative study."""
from collections import Counter
from app.main import analyze_sentiment, analyze_document

SENTIMENT_GOLD = [
    ("The project achieved excellent results and successful growth.", "positive"),
    ("The team improved the system and users are happy.", "positive"),
    ("The release failed and caused serious damage.", "negative"),
    ("The decision created risk and several problems.", "negative"),
    ("The meeting is scheduled for Monday.", "neutral"),
    ("The report describes three companies and two products.", "neutral"),
    ("The result is not good.", "negative"),
    ("The change is not harmful.", "positive"),
]
RELATION_GOLD_TEXT = "Steve Jobs founded Apple. NASA launched Apollo 11. Marie Curie discovered radium."
RELATION_GOLD = {("Steve Jobs", "FOUND", "Apple"), ("NASA", "LAUNCH", "Apollo 11"), ("Marie Curie", "DISCOVER", "radium")}

def score(gold, predicted):
    tp=sum(g==p for g,p in zip(gold,predicted)); labels=set(gold)|set(predicted)
    # Macro one-vs-rest precision/recall/F1.
    rows=[]
    for label in labels:
        ltp=sum(g==label and p==label for g,p in zip(gold,predicted)); fp=sum(g!=label and p==label for g,p in zip(gold,predicted)); fn=sum(g==label and p!=label for g,p in zip(gold,predicted))
        pr=ltp/(ltp+fp) if ltp+fp else 0; re=ltp/(ltp+fn) if ltp+fn else 0
        rows.append((pr,re,2*pr*re/(pr+re) if pr+re else 0))
    return {"accuracy":tp/len(gold) if gold else 0,"macro_precision":sum(x[0] for x in rows)/len(rows),"macro_recall":sum(x[1] for x in rows)/len(rows),"macro_f1":sum(x[2] for x in rows)/len(rows)}

def main():
    sg=[label for _,label in SENTIMENT_GOLD]; sp=[analyze_sentiment(text)["label"] for text,_ in SENTIMENT_GOLD]
    result=analyze_document(RELATION_GOLD_TEXT,"evaluation.txt")
    rp={(t["subject"],t["predicate"],t["object"]) for t in result["triples"]}
    tp=len(rp & RELATION_GOLD); precision=tp/len(rp) if rp else 0; recall=tp/len(RELATION_GOLD)
    print("Sentiment",score(sg,sp))
    print("Relations",{"gold":len(RELATION_GOLD),"predicted":len(rp),"precision":precision,"recall":recall,"f1":2*precision*recall/(precision+recall) if precision+recall else 0})
    print("Caution: tiny hand-labelled smoke set; metrics are illustrative, not statistically representative.")
if __name__=="__main__": main()
