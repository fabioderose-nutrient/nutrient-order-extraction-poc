import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from contextlib import contextmanager


@contextmanager
def native_output_to_stderr():
    """The SDK's native code prints status lines (license notice, model loading) on stdout.
    Send them to stderr so that stdout only carries the extraction result."""
    sys.stdout.flush()
    saved = os.dup(1)
    os.dup2(2, 1)
    try:
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved, 1)
        os.close(saved)


with native_output_to_stderr():
    import nutrient_sdk as ns

HEADER_FIELDS = ("supplier", "orderNumber", "orderDate", "customerNumber")
LINE_FIELDS = (
    "position",
    "partNumber",
    "customerPartNumber",
    "description",
    "quantity",
    "unit",
    "unitPrice",
    "totalPrice",
    "deliveryDate",
)
# The instructions and schema.json name the usual English labels and their German equivalents
# (in parentheses), so the same extraction works on English and German order confirmations.
INSTRUCTIONS = (
    "The document is an order confirmation (order acknowledgement, Auftragsbestätigung) sent by a supplier to its customer. "
    "orderNumber is the supplier's own confirmation number (Order confirmation no., Acknowledgement no., Sales order no., "
    "Our reference; German: Auftragsbestätigung Nr., AB-Nr., Beleg-Nr., Bestellbestätigung Nr.), "
    "never the customer's purchase order number (Your order, Your PO, Customer PO, Purchase order; "
    "German: Ihre Bestellung, Ihre Bestell-Nr., Bestellung Nr.). "
    "customerNumber is the number the supplier assigned to the customer (Customer no., Customer number, Account no.; "
    "German: Kundennummer, Kunden-Nr., Kd.-Nr.). "
    "orderDate is the date of the confirmation (Date, Document date, Acknowledgement date; German: Datum, Belegdatum, "
    "AB-Datum), never the date of the customer's order. "
    "Return amounts and quantities as plain numbers with a dot as decimal separator and no thousands separator "
    "(1,234.50 and 1.234,50 both become 1234.50; 1,000 pcs and 1.000 Stk both become 1000). "
    "Copy every date and calendar week character by character exactly as printed: 02/10/2026 stays 02/10/2026, "
    "07.10.2026 stays 07.10.2026, CW 42/2026 stays CW 42/2026, KW 42/2026 stays KW 42/2026. "
    "Never convert dates to another format. "
    "Create exactly one lineItems entry per position number in the item table. The table may have no ruling lines and a "
    "position can span several text lines: every line printed below a position number and above the next position number "
    "belongs to that position. Within such a position, the line with the customer's part number (Your part no., Customer "
    "part no., Customer article; German: Ihre Artikel-Nr., Kd.-Art.-Nr., Ihre Materialnummer) goes only into "
    "customerPartNumber and the delivery line (Delivery date, Delivery week; German: Liefertermin, Lieferdatum, "
    "Lieferwoche, KW) goes only into deliveryDate; description contains the remaining description lines only. "
    "Use an empty string for text fields that are not printed."
)
NUL_ESCAPE = re.compile("\x00([0-9a-fA-F]{2})")
# Customer part number and delivery lines that the model left inside the description (English and German labels).
CUSTOMER_PART = re.compile(
    r"\s*(?:(?:Your|Customer|Cust\.)\s+(?:part|article|item|material)(?:\s*(?:no\.?|number|#))?"
    r"|(?:Ihre|Kunden|Kd\.)[ -]?(?:Artikel|Art\.|Material)[ -]?(?:Nr\.?|nummer))\s*:?\s*(\S+)",
    re.IGNORECASE,
)
DELIVERY = re.compile(
    r"\s*(?:Delivery\s+(?:date|week)|Ship\s+date|Liefertermin|Lieferdatum|Lieferwoche|Liefer-KW)\s*:?\s*"
    r"((?:(?:KW|CW|Week)\s*)?[0-9][0-9./ -]*[0-9])",
    re.IGNORECASE,
)


def clean(value):
    if isinstance(value, str):
        return NUL_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), value)
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Extract line items from an order confirmation PDF with a local model.")
    parser.add_argument("input")
    parser.add_argument("--format", choices=("json", "csv", "delimited"), default="json")
    parser.add_argument("--separator", default=";")
    parser.add_argument("--out")
    parser.add_argument("--endpoint", default=os.environ.get("AI_ENDPOINT", "http://localhost:11434/v1"))
    parser.add_argument("--model", default=os.environ.get("AI_MODEL", "qwen2.5:7b-instruct"))
    parser.add_argument("--schema", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json"))
    parser.add_argument("--confidence", action="store_true")
    parser.add_argument("--no-strict", action="store_true")
    return parser.parse_args(argv)


def check_endpoint(endpoint):
    try:
        with urllib.request.urlopen(endpoint.rstrip("/") + "/models", timeout=5):
            return
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise ConnectionError(f"model endpoint unreachable at {endpoint}: {error}")


def build_settings(args):
    settings = ns.DocumentSettings()
    settings.vision_settings.engine = ns.VisionEngine.ICR
    ai = settings.ai_processing_settings
    ai.provider = "local"
    ai.endpoint = args.endpoint
    ai.model = args.model
    ai.temperature = 0.0
    ai.include_source_locations = args.confidence
    ai.include_confidence = args.confidence
    ai.strict_structured_output = not args.no_strict
    return settings


def extract(input_path, args, schema_envelope):
    with ns.Document.open(input_path, build_settings(args)) as document:
        request = ns.StructuredExtractionRequest()
        request.schema = json.dumps(schema_envelope)
        request.instructions = INSTRUCTIONS
        raw = ns.Vision.set(document).extract_structured(request)
    return clean(json.loads(raw))


def format_value(value, separator=None):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    else:
        text = str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    if separator:
        text = text.replace(separator, " ")
    return text


def tidy_item(item):
    description = item.get("description") or ""
    for pattern, field in ((CUSTOMER_PART, "customerPartNumber"), (DELIVERY, "deliveryDate")):
        match = pattern.search(description)
        if match:
            if not item.get(field):
                item[field] = match.group(1)
            description = (description[: match.start()] + " " + description[match.end() :]).strip()
    item["description"] = re.sub(r"\s+", " ", description)
    return item


def tidy(extraction):
    extraction["lineItems"] = [tidy_item(item) for item in extraction.get("lineItems") or [] if isinstance(item, dict)]
    return extraction


def rows(extraction):
    header = [extraction.get(field) for field in HEADER_FIELDS]
    for item in extraction.get("lineItems") or []:
        yield header + [item.get(field) for field in LINE_FIELDS]


def to_csv(extraction):
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", lineterminator="\r\n")
    writer.writerow(HEADER_FIELDS + LINE_FIELDS)
    for row in rows(extraction):
        writer.writerow([format_value(v) for v in row])
    return buffer.getvalue()


def to_delimited(extraction, separator):
    lines = [separator.join(format_value(v, separator) for v in row) for row in rows(extraction)]
    return "".join(line + "\r\n" for line in lines)


def split_result(result):
    if "extraction" in result:
        return tidy(result.get("extraction") or {}), result.get("metadata") or {}
    return tidy(result), {}


def render(result, args):
    extraction, metadata = split_result(result)
    if args.format == "csv":
        return to_csv(extraction), "utf-8-sig"
    if args.format == "delimited":
        return to_delimited(extraction, args.separator), "utf-8-sig"
    payload = {"extraction": extraction, "metadata": metadata} if args.confidence else extraction
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8"


def write_output(text, encoding, out):
    if out:
        with open(out, "w", encoding=encoding, newline="") as handle:
            handle.write(text)
    else:
        sys.stdout.buffer.write(text.encode(encoding))
        sys.stdout.buffer.flush()


def register_license():
    """Register NUTRIENT_LICENSE_KEY. Without it the SDK runs in evaluation mode."""
    key = os.environ.get("NUTRIENT_LICENSE_KEY", "").strip()
    if key:
        ns.License.register_key(key)


def main(argv=None):
    args = parse_args(argv)
    try:
        check_endpoint(args.endpoint)
        with open(args.schema, encoding="utf-8") as handle:
            schema_envelope = json.load(handle)
        with native_output_to_stderr():
            register_license()
            result = extract(args.input, args, schema_envelope)
        text, encoding = render(result, args)
        write_output(text, encoding, args.out)
    except (ns.NutrientException, ConnectionError, OSError, ValueError) as error:
        sys.stderr.write(f"error: {str(error).splitlines()[0] if str(error) else type(error).__name__}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
