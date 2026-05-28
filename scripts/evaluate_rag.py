import argparse
import json
from datetime import datetime
from pathlib import Path

import requests


def load_questions(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def query_backend(base_url, document_id, question):
    response = requests.post(
        f"{base_url.rstrip('/')}/query/",
        json={
            "question": question,
            "document_id": document_id,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def contains_all(text, keywords):
    normalized = text.lower()
    return all(keyword.lower() in normalized for keyword in keywords)


def any_source_page_match(sources, expected_pages):
    if not expected_pages:
        return True

    source_pages = {source.get("page_number") for source in sources}
    return any(page in source_pages for page in expected_pages)


def evaluate_case(case, result):
    answer = result.get("answer", "")
    context_text = "\n\n".join(result.get("context_used", []))
    sources = result.get("sources", [])
    metrics = result.get("metrics", {})

    expected_answer_keywords = case.get("expected_answer_keywords", [])
    expected_context_keywords = case.get("expected_context_keywords", [])
    expected_source_pages = case.get("expected_source_pages", [])

    answer_keyword_pass = contains_all(answer, expected_answer_keywords)
    context_keyword_hit = contains_all(context_text, expected_context_keywords)
    source_page_hit = any_source_page_match(sources, expected_source_pages)

    not_found_pass = True
    if case.get("should_be_not_found"):
        not_found_pass = "not found" in answer.lower() or "no relevant information" in answer.lower()

    passed = answer_keyword_pass and context_keyword_hit and source_page_hit and not_found_pass

    return {
        "id": case.get("id"),
        "question": case["question"],
        "passed": passed,
        "checks": {
            "answer_keyword_pass": answer_keyword_pass,
            "context_keyword_hit": context_keyword_hit,
            "source_page_hit": source_page_hit,
            "not_found_pass": not_found_pass,
        },
        "answer": answer,
        "sources": sources,
        "metrics": metrics,
    }


def summarize(results):
    total = len(results)
    passed = sum(1 for result in results if result["passed"])

    def rate(check_name):
        if total == 0:
            return 0
        hits = sum(1 for result in results if result["checks"][check_name])
        return round((hits / total) * 100, 2)

    latencies = [
        result["metrics"].get("total_latency_ms")
        for result in results
        if result.get("metrics") and result["metrics"].get("total_latency_ms") is not None
    ]

    return {
        "total": total,
        "passed": passed,
        "pass_rate": round((passed / total) * 100, 2) if total else 0,
        "answer_keyword_rate": rate("answer_keyword_pass"),
        "context_keyword_hit_rate": rate("context_keyword_hit"),
        "source_page_hit_rate": rate("source_page_hit"),
        "not_found_pass_rate": rate("not_found_pass"),
        "avg_total_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
    }


def write_report(output_path, report):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def print_summary(summary, results):
    print("\nRAG Evaluation Summary")
    print("----------------------")
    print(f"Total cases: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Pass rate: {summary['pass_rate']}%")
    print(f"Answer keyword rate: {summary['answer_keyword_rate']}%")
    print(f"Context keyword hit rate: {summary['context_keyword_hit_rate']}%")
    print(f"Source page hit rate: {summary['source_page_hit_rate']}%")
    print(f"Not-found pass rate: {summary['not_found_pass_rate']}%")
    if summary["avg_total_latency_ms"] is not None:
        print(f"Average total latency: {summary['avg_total_latency_ms']} ms")

    print("\nCase Results")
    print("------------")
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status} {result['id']}: {result['question']}")
        if not result["passed"]:
            print(f"  checks={result['checks']}")
            print(f"  answer={result['answer']}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate DocuMind-AI RAG retrieval and answer grounding.")
    parser.add_argument("--document-id", required=True, help="Document ID returned by /ingest or shown in the UI.")
    parser.add_argument(
        "--questions",
        default="ai/evaluation/documind_test_pdf_questions.json",
        help="Path to evaluation questions JSON.",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL.")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    questions = load_questions(args.questions)
    results = []

    for case in questions:
        result = query_backend(args.base_url, args.document_id, case["question"])
        results.append(evaluate_case(case, result))

    summary = summarize(results)
    report = {
        "created_at": datetime.now().isoformat(),
        "document_id": args.document_id,
        "questions_file": args.questions,
        "summary": summary,
        "results": results,
    }

    print_summary(summary, results)

    if args.output:
        write_report(Path(args.output), report)
        print(f"\nWrote report: {args.output}")


if __name__ == "__main__":
    main()
