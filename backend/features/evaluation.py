# features/evaluation.py
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset
from retrieval.multi_query import multi_query_search
from agent.graph import run_agent

def evaluate_rag(query: str, user_id: int):
    """Evaluate RAG quality for a given query"""
    try:
       
        chunks = multi_query_search(query, user_id)
        contexts = [c["content"] for c in chunks]

   
        answer = run_agent(query, user_id)

       
        data = {
            "question": [query],
            "answer": [answer],
            "contexts": [contexts],
        }

        dataset = Dataset.from_dict(data)

       
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
            ]
        )

        return {
            "query": query,
            "faithfulness": round(float(result["faithfulness"]), 2),
            "answer_relevancy": round(float(result["answer_relevancy"]), 2),
            "context_precision": round(float(result["context_precision"]), 2),
        }

    except Exception as e:
        return {"error": str(e)}