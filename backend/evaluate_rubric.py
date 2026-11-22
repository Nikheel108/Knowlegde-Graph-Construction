"""Small reproducible evaluation; illustrative only, not a representative benchmark."""
from app.nlp_features import analyze_sentiment
SENTIMENT_GOLD = [
("The project achieved excellent results and successful growth.","positive"),("The team improved the system and users are happy.","positive"),("The product is great and effective.","positive"),("The company supports beneficial innovation.","positive"),("The launch was a success.","positive"),("The new plan improved services.","positive"),("The release failed and caused serious damage.","negative"),("The decision created risk and several problems.","negative"),("The crisis caused a major loss.","negative"),("The system is poor and harmful.","negative"),("The project failed after difficult delays.","negative"),("The results show a decline and concerns.","negative"),("The meeting is scheduled for Monday.","neutral"),("The report describes three companies and two products.","neutral"),("A researcher published a report in 2024.","neutral"),("The document contains five sections.","neutral"),("The team discussed the plan yesterday.","neutral"),("The company operates in three countries.","neutral"),("The result is not good.","negative"),("The change is not harmful.","positive"),("The service is not effective.","negative"),("The outcome was not poor.","positive"),("The proposal is neither good nor bad.","neutral"),("The team reported no success.","negative"),("Great, another outage.","negative"),("The product is good but the service failed.","neutral"),("The system is not bad.","positive"),("The project is not successful.","negative")]
def classification_metrics(gold,predicted):
 labels=sorted(set(gold)|set(predicted)); rows=[]
 for label in labels:
  tp=sum(g==label and p==label for g,p in zip(gold,predicted)); fp=sum(g!=label and p==label for g,p in zip(gold,predicted)); fn=sum(g==label and p!=label for g,p in zip(gold,predicted)); pr=tp/(tp+fp) if tp+fp else 0; re=tp/(tp+fn) if tp+fn else 0; rows.append((pr,re,2*pr*re/(pr+re) if pr+re else 0))
 return {"n":len(gold),"accuracy":sum(g==p for g,p in zip(gold,predicted))/len(gold),"macro_precision":sum(r[0] for r in rows)/len(rows),"macro_recall":sum(r[1] for r in rows)/len(rows),"macro_f1":sum(r[2] for r in rows)/len(rows)}
def main():
 gold=[label for _,label in SENTIMENT_GOLD]; pred=[analyze_sentiment(text)["label"] for text,_ in SENTIMENT_GOLD]; print("Sentiment lexicon",classification_metrics(gold,pred))
 from app.nlp_features import topic_model, tfidf_features
 corpus=[{"filename":"space.txt","sentences":["NASA launched a space mission","The rocket explored space"]},{"filename":"climate.txt","sentences":["Solar energy reduces emissions","Climate action supports clean energy"]}]
 print("Topic model smoke check", {"topics":len(topic_model(corpus)),"documents":len(corpus),"tfidf_vocabulary":tfidf_features(corpus[0]["sentences"])["vocabulary_size"]})
 try:
  from app.main import analyze_document
  text="Steve Jobs founded Apple. NASA launched Apollo 11. Marie Curie discovered radium."; expected={("Steve Jobs","FOUND","Apple"),("NASA","LAUNCH","Apollo 11"),("Marie Curie","DISCOVER","radium")}; actual={(t["subject"],t["predicate"],t["object"]) for t in analyze_document(text,"evaluation.txt")["triples"]}; tp=len(actual&expected); pr=tp/len(actual) if actual else 0; re=tp/len(expected); print("Information extraction",{"gold":len(expected),"predicted":len(actual),"precision":pr,"recall":re,"f1":2*pr*re/(pr+re) if pr+re else 0})
 except Exception as exc: print("Information extraction evaluation unavailable:",type(exc).__name__)
 print("Limit: hand-labelled demo set only; expand and independently annotate it before making general accuracy claims.")
if __name__=="__main__": main()
