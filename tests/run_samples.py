import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import extract_order

FIELDS = extract_order.HEADER_FIELDS + extract_order.LINE_FIELDS


def empty_fields(extraction):
    count = 0
    for field in extract_order.HEADER_FIELDS:
        if extraction.get(field) in (None, ""):
            count += 1
    for item in extraction.get("lineItems") or []:
        for field in extract_order.LINE_FIELDS:
            if item.get(field) in (None, ""):
                count += 1
    return count


def main(argv=None):
    args = extract_order.parse_args((argv if argv is not None else sys.argv[1:]) + [os.path.join(ROOT, "samples")])
    samples_dir = args.input
    output_dir = os.path.join(samples_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    extract_order.check_endpoint(args.endpoint)
    extract_order.register_license()
    with open(args.schema, encoding="utf-8") as handle:
        schema_envelope = json.load(handle)
    summary = []
    for pdf in sorted(glob.glob(os.path.join(samples_dir, "*.pdf"))):
        name = os.path.splitext(os.path.basename(pdf))[0]
        started = time.time()
        try:
            with extract_order.native_output_to_stderr():
                result = extract_order.extract(pdf, args, schema_envelope)
            extraction, metadata = extract_order.split_result(result)
            with open(os.path.join(output_dir, name + ".json"), "w", encoding="utf-8") as handle:
                json.dump({"extraction": extraction, "metadata": metadata} if args.confidence else extraction, handle, ensure_ascii=False, indent=2)
            with open(os.path.join(output_dir, name + ".txt"), "w", encoding="utf-8-sig", newline="") as handle:
                handle.write(extract_order.to_delimited(extraction, args.separator))
            summary.append((name, len(extraction.get("lineItems") or []), empty_fields(extraction), round(time.time() - started, 1), ""))
        except Exception as error:
            summary.append((name, 0, 0, round(time.time() - started, 1), str(error).splitlines()[0]))
    width = max([len(s[0]) for s in summary] + [4])
    lines = [f"{'file':<{width}}  items  empty  seconds  error"]
    for name, items, empty, seconds, error in summary:
        lines.append(f"{name:<{width}}  {items:>5}  {empty:>5}  {seconds:>7}  {error}")
    report = "\n".join(lines) + "\n"
    sys.stdout.write(report)
    with open(os.path.join(output_dir, "summary.txt"), "w", encoding="utf-8") as handle:
        handle.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
