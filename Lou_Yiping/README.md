# Quick Win CLI Toolkit

Terminal utilities for extracting “quick win” PGN matches in line with `实现方案落地.txt`:

## Features
- Parses batches of PGN games.
- Filters by rating range, move count, and per-move evaluation drops (threshold 60 cp by default).
- Uses a Stockfish-compatible engine to evaluate each move.
- Outputs qualifying games as a single PGN file and prints a human-readable summary.

## Getting Started

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the CLI**

   ```bash
   python quick_win_cli.py sample.pgn --output quick_wins.pgn
   ```

   Use `--engine-path` to point to your Stockfish binary if it is not on `$PATH`.

3. **Inspect results**
   - Summary is emitted to the terminal.
   - Qualifying PGNs are consolidated into the provided `--output` file.
   - Optionally use `--metadata quick_wins.json` for JSON metadata.

## Advanced Options

- `--min-rating` / `--max-rating` — filter players by rating.
- `--max-moves` — drop games longer than the limit.
- `--max-errors` — maximum allowable errors for the winner (default 1).
- `--depth` and `--threshold-cp` — engine depth and cp drop threshold.
- `--max-results` — cap how many matches are gathered.

Refer to `quick_win_cli.py --help` for the full list of options.
