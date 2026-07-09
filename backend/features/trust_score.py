TRUST_SCORES = {
    "arxiv.org": 95,
    "research": 90,
    "github.com": 85,
    "docs": 90,
    "youtube": 70,
    "medium.com": 60,
    "reddit.com": 40,
    "blog": 55,
    "pdf": 85,
    "word": 80,
    "csv": 75,
    "ocr": 65,
    "pptx": 75,
    "markdown": 70,
    "website": 65,
    "web": 50
}

def get_trust_score(metadata: dict):
    source_type = metadata.get("source_type", "")
    source_url = metadata.get("source_url", "")

   
    for domain, score in TRUST_SCORES.items():
        if domain in source_url.lower():
            return score

   
    return TRUST_SCORES.get(source_type, 50)

def add_trust_scores(results: list):
    for result in results:
        result["trust_score"] = get_trust_score(result.get("metadata", {}))
    return results