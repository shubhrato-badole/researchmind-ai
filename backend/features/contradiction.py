import re 


def local_contradiction_check(chunks:list):

    if len(chunks) < 2:
        return None
    

    number_pattern = re.compile(r'\b\d+\.?\d*\b')

    source_numbers = {}
    for chunk in chunks :
     source = chunk("metadata" , {}).get("filename", "unknown")
     content = chunk["content"].lower()

     words = content.split()
     for i , words in enumerate(words):
        numbers = number_pattern.findall(words)
        if numbers:
           start = max(0 , i-3)
           end = min(len(words), i+4 )
           context = " ".join(words[start:end])

           if source not in source_numbers:
              source_numbers[source]=[]
              source_numbers[source].append({
                  "number": numbers[0],
                  "context": context
              })
    sources = list(source_numbers.keys())

    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            source_a = sources[i]
            source_b = sources[j]
            
            nums_a = source_numbers[source_a]
            nums_b = source_numbers[source_b]

            for num_a in nums_a:
                for num_b in nums_b:
                    # same context but different numbers = contradiction
                    context_a = set(num_a["context"].split())
                    context_b = set(num_b["context"].split())
                    overlap = context_a.intersection(context_b)
                    
                    if (
                        len(overlap) >= 2 and  # similar context
                        num_a["number"] != num_b["number"]  # different numbers
                    ):
                        return {
                            "type": "number_conflict",
                            "source_a": source_a,
                            "source_b": source_b,
                            "message": f"{source_a} mentions {num_a['number']} but {source_b} mentions {num_b['number']} in similar context: '{num_a['context']}'"
                        }

    return None

def detect_contradictions(query: str, chunks: list):
    """main contradiction detector — local first, flag for LLM"""
    
    if len(chunks) < 2:
        return None

  
    local_result = local_contradiction_check(chunks)
    
    if local_result:
        return local_result

    return None