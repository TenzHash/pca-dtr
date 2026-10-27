# Biometric DTR & CSC Form No. 48 Generator (prototype)

Reads ZKTeco "Attendance Record Report" exports (.xls / .xlsx) and prints CSC Form No. 48 DTRs
on blank 8.5" x 11" portrait paper. Runs fully offline at each office.

## Production app (one per office, offline)
    python desktop.py    # native window; or double-click DTR_Generator.exe (build with build_exe.bat)
    python app.py        # same app in the browser instead
Opens its own window (needs Microsoft Edge WebView2, built into Windows 11 and current Windows 10; otherwise it falls back to the browser): choose the office, drop in the ZKTeco exports,
pick a month, review every employee (flags for incomplete punches), add Leave / Official Business
remarks per date range, preview each DTR, then download all DTRs (PDF), individual PDFs (ZIP) or the
HR summary (Excel). Everything is stored in a `DTR_Data` folder beside the program - copy it to back up.
`python test_app.py <folder> [roster.xlsx]` runs an end-to-end check.

## Command line (same engine)
    pip install -r requirements.txt
    python generate_dtr.py --input Attendance --office regional --month 2026-08 \
           --roster Biometrics.xlsx --remarks remarks_sample.csv
Outputs: `output/DTR_<office>_<YYYY-MM>.pdf` (one page per employee) and `..._summary.xlsx`
(monthly totals for salary processing + daily detail + "days to review" flags).

Useful options: `--office catanduanes|camarines-norte|naga|iriga|masbate|sorsogon|regional`,
`--employee "Santos"`, `--individual` (one PDF each), `--utility "Name1,Name2"`,
`--holidays 2026-12-30`, `--in-charge "NAME"`, `--ot-threshold 30`. `python tests.py` checks the rules.

## Rules implemented
| Schedule | Required |
|---|---|
| Provincial | Mon-Fri 8:00-5:00 fixed |
| Regional flexitime | In/Out windows per weekday; required out = arrival + 9h (8h work + 1h lunch), kept inside the out window |
| Utility | Mon-Thu 7:00-4:00, Fri 8:00-5:00 |
Undertime = late arrival + early departure + lunch beyond 60 min. Overtime = departure past the latest official out-time.

## Handling of real-world punch data
- Concatenated strings (`07:4917:25`) are split with `\d{2}:\d{2}`; double scans (<3 min apart) collapse.
- First punch = AM arrival, last = PM departure; lunch punches used when present, otherwise 12:00 / 1:00 are filled in.
- Lone punch -> NO TIME-OUT / NO TIME-IN (late still computed); AM-only / PM-only -> HALF-DAY. All are flagged for review.
- Holidays: weekdays where almost nobody punched are auto-detected (matched real holidays in the sample data); add others with `--holidays`.
- Several files for one month (e.g. `June 1-15.xls` + `Attendance 202606.xls`) are merged.
- Leave / Official Business / Travel: list them in a CSV (`employee,date,remark`, dates may be `start:end`, `*` = everyone) so days without punches don't print as ABSENT.
- Employees are matched to the HR roster by normalized name (full names, utility detection). Only name/position columns are read.

## Notes
`.xls` is read with `xlrd`; if it is not installed the tool falls back to LibreOffice for conversion.

## Installer (Setup.exe)
`installer.iss` (Inno Setup) + `.github/workflows/build-installer.yml` build `DTR_Generator_Setup.exe` in the cloud:
upload this folder (without any attendance data) to a GitHub repository, open the Actions tab, run "Build installer",
download the artifact. The installer needs no admin rights, adds Start menu / desktop shortcuts and an uninstaller.
Installed copies keep their data in Documents\DTR Generator (kept when uninstalling).

## Releasing an update to all offices
1. Raise `VERSION` in `version.py` (e.g. 1.0.1), upload the changed files to GitHub, run **Build installer**.
2. Download the artifact `DTR_Generator_Release`: it holds `DTR_Generator_Setup.exe` and `latest.json` (with a SHA-256 check).
3. Put both files in ONE place every office can read: a shared network folder, or any web address
   (for GitHub use a separate public "releases" repository that holds only these two files; do not make the code repository public).
4. In each office's app: **Files & Roster > Updates**, paste the folder path or the web address of `latest.json` once.
   From then on the app checks at startup and shows a gold "Update available - install" button. Data is kept (it lives in Documents\DTR Generator).

## Code signing (removes "Windows protected your PC")
Needs a code-signing certificate bought from a certificate authority. Add repository secrets `SIGN_PFX_BASE64` (the .pfx file, base64) and
`SIGN_PFX_PASSWORD`; the workflow then signs the program and the installer automatically. Note: new certificates are usually issued on hardware or
cloud-signing services and cannot be exported as a .pfx; with those, replace the two signing steps with the provider's GitHub Action.

## Backup & restore
**Files & Roster > Backup & restore**: "Back up now" downloads a .zip (attendance, roster, remarks, edits, signatures, settings);
"Restore" loads one on any PC (a safety copy of the current data is kept first). A daily automatic backup (last 10) is kept in `DTR_Data\backups`.

### Setting the update location once (administrator)
Edit `update_source.txt` in the repository: write the shared folder or web address of `latest.json` on one line. The installer copies it to every PC,
so office staff only see a plain "Check for updates" button (and a gold button when an update exists). Staff can still override it under "Administrator options".
