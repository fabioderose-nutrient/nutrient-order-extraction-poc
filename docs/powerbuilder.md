# Calling the extractor from PowerBuilder

The extractor is a command line tool. PowerBuilder starts it, waits for it to finish, then reads the result file. The delimited format gives one line per position with the header fields repeated on every line, so it can be parsed like any delimited string.

Field order per line (separator `;` by default):

```text
supplier;orderNumber;orderDate;customerNumber;position;partNumber;
customerPartNumber;description;quantity;unit;unitPrice;totalPrice;deliveryDate
```

The result file is UTF-8 with a byte order mark. `FileOpen` with `EncodingUTF8!` reads it and skips the mark.

## Minimal example

A synchronous call that loads the result into a datastore. The example assumes the extractor is installed in `C:\nutrient-order-extraction-poc`.

```text
// Local external function declaration (kernel32), once per application:
// SUBROUTINE Sleep(ulong dwMilliseconds) LIBRARY "kernel32.dll"

// ds_items: datastore with 13 string columns in the field order above
string ls_pdf, ls_out, ls_cmd, ls_line
integer li_file, li_row, li_pos, li_col
long ll_rc

ls_pdf = "C:\Documents\order-confirmation.pdf"
ls_out = "C:\Temp\order-confirmation.txt"
ls_cmd = "cmd /c ""C:\nutrient-order-extraction-poc\run_extract.bat"" """ + ls_pdf + &
         """ --format delimited --out """ + ls_out + """"

FileDelete(ls_out)
ll_rc = Run(ls_cmd, Minimized!)
IF ll_rc <> 1 THEN
   MessageBox("Extraction", "Could not start the extractor")
   RETURN
END IF

// Run() returns immediately; wait until the output file exists
DO WHILE NOT FileExists(ls_out)
   Yield()
   Sleep(500)
LOOP

li_file = FileOpen(ls_out, LineMode!, Read!, LockRead!, Replace!, EncodingUTF8!)
IF li_file < 0 THEN RETURN
ds_items.Reset()
DO WHILE FileRead(li_file, ls_line) > 0
   IF Trim(ls_line) = "" THEN CONTINUE
   li_row = ds_items.InsertRow(0)
   li_col = 1
   li_pos = Pos(ls_line, ";")
   DO WHILE li_pos > 0 AND li_col < 13
      ds_items.SetItem(li_row, li_col, Left(ls_line, li_pos - 1))
      ls_line = Mid(ls_line, li_pos + 1)
      li_col++
      li_pos = Pos(ls_line, ";")
   LOOP
   ds_items.SetItem(li_row, 13, ls_line)
LOOP
FileClose(li_file)
```

## Notes

- The output file is written in one go at the end of the extraction, so `FileExists` is a safe completion signal. For the exit code, use a wrapper `.bat` that redirects stderr to a second file and writes `%ERRORLEVEL%` to a third file, or call the tool with `ShellExecuteEx` and `WaitForSingleObject` through external function declarations.
- Expect 1 to 3 minutes per document on a CPU-only PC. Keep the call asynchronous so the UI does not block, for example with a Timer event that polls the output file.
- With PowerBuilder 2019 R3 or later you can use `--format json` and `JsonParser` instead. The JSON has the same fields with number types, plus an optional `metadata` node (`--confidence`) with a per-field confidence score to highlight doubtful values.
