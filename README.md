# 🎵 Music Library Fingerprint Organizer  
*A fingerprint‑based identification and metadata‑normalization system for large music collections*

---

## 📌 Overview  
This project is a **personal, non‑commercial tool** designed to clean, organize, and normalize music libraries.  
Its primary goal is to **identify audio files based on their acoustic fingerprint**, not their filenames or embedded tags, which are often incomplete, inconsistent, or incorrect.

Once a track is correctly identified, the system retrieves canonical metadata from **MusicBrainz**, verifies consistency, and rewrites tags and filenames using a standardized naming scheme.

The result is a clean, searchable, deduplicated, and fully normalized music archive.

---

## 🔍 Why Fingerprinting?  
Most large music collections suffer from:

- incorrect or missing tags  
- inconsistent naming conventions  
- typos, watermarks, branding, or junk text  
- mismatched artist/title/album fields  
- duplicate files with different names  
- inconsistent folder structures  

Relying on filenames or tags alone is unreliable.  
This project instead uses **Chromaprint fingerprints** to determine the *actual* identity of each audio file.

---

## 🧠 Core Workflow  
The system processes each audio file using the following pipeline:

1. **Fingerprint Extraction**  
   - Uses Chromaprint (`fpcalc`) to generate an acoustic fingerprint and duration.

2. **External Identification (AcoustID)**  
   - The fingerprint is sent to an external fingerprint database (AcoustID) to obtain the correct **MBID** (MusicBrainz Recording ID).  
   - This step provides a trusted identity for the audio content, independent of filenames or tags.

3. **Metadata Retrieval (MusicBrainz)**  
   - With the MBID, the system fetches canonical metadata:
     - title  
     - artist(s)  
     - album / release group  
     - track number  
     - release date  
     - additional identifiers  

4. **Verification & Cross‑Checking**  
   - The system compares:
     - fingerprint‑based identity  
     - existing tags  
     - filename  
     - folder structure  
   - Any mismatches are flagged or corrected.

5. **Normalization**  
   - Tags are rewritten using a consistent, complete, and verified metadata set.  
   - Filenames and folder paths are rebuilt using a standardized naming convention.

6. **Database Storage**  
   - All processed files are stored in a local database for:
     - fast searching  
     - duplicate detection  
     - snapshot/backup management  

---

## 🗂 Features  
- ✔ Fingerprint‑based track identification  
- ✔ MBID lookup and MusicBrainz metadata integration  
- ✔ Automatic tag correction and completion  
- ✔ Filename and folder normalization  
- ✔ Duplicate detection using fingerprints + metadata  
- ✔ Snapshot and backup support  
- ✔ Local database for fast queries  
- ✔ Designed for very large libraries (multi‑TB scale)

---

## 🧩 Requirements  
See `requirements.txt` for Python dependencies.  
External tools required:

- **Chromaprint / fpcalc** (for fingerprint generation)

---

## 📦 Status  
This project is being developed and refined.  
It is intended for personal use but may be useful to others with large, messy music libraries.

---

## 📬 Contact  
If you have questions or suggestions, feel free to open an issue or contact me.

---

# **Project Components & Current Implementation Status**

## 🔧 Verification & Cross‑Checking (Work in Progress)

The long‑term goal is to ensure that **file content, tags, filenames, and folder structure all refer to the same recording**.  
This stage is **partially implemented** and still evolving.

### **What the system *will* compare**
- **Fingerprint‑based identity**  
  *Not implemented yet — requires AcoustID lookup access to retrieve MBIDs.*

- **Existing embedded tags**  
  *Partially implemented — tags are read in a separate script but not yet integrated into the main pipeline.*

- **Filename**  
  *Implemented — filenames are parsed and compared as part of the file‑mapping logic.*

- **Folder structure**  
  *Implemented — handled through the filemap comparison engine.*

### **Mismatch handling**
- **Flagging or correcting mismatches**  
  *Not implemented yet — planned once fingerprint lookup and tag integration are complete.*

---

## 🧹 Normalization (Partially Implemented)

Normalization aims to produce a **clean, consistent, verified** library.

### **What is planned**
- Rewrite tags using complete, verified metadata  
- Rebuild filenames and folder paths using a standardized naming convention  
- Ensure consistency between:
  - audio content  
  - tags  
  - filenames  
  - folder structure  

### **What is implemented now**
- Basic normalization logic exists but **lacks verified metadata**, since fingerprint‑based identification is not yet available.
- File renaming and tag rewriting are **partially implemented** and depend on future MBID lookup integration.

---

# **Project Structure & Components**

Below is a summary of the key scripts and modules included in the repository.

## 📁 **app_search_music_brainz.py**
A small textual/CLI application used to test the **MusicBrainz search pipeline**.

Features:
- Search for artists, songs, and albums directly from MusicBrainz  
- Validate that MB search and API integration work correctly  
- Useful for testing metadata retrieval independently of fingerprinting  

---

## 📁 **app_fingerprint_files.py**
A small textual/CLI application used to test the **fingerprinting pipeline**.

Features:
- Opens the custom textual file explorer to select audio files  
- Generates Chromaprint fingerprints  
- Sends fingerprints to the fingerprint server (audiofp-server)  
- Prints the results returned by the fingerprint engine  
- Used to validate the fingerprint extraction and lookup workflow  

---

## 🦀 **audiofp-server (Rust)**
A standalone Rust server that wraps the **audio-fp** fingerprinting library.

Responsibilities:
- Provides a local API endpoint for fingerprint generation  
- Handles communication with the Chromaprint engine  
- Designed to be fast, safe, and scalable  
- Fully documented in its own section of the repository  

---

## ⚙️ **config.template.yaml**
Configuration template for the entire system.

To use:
1. Rename to `config.yaml`  
2. Fill in:
   - API keys (AcoustID, MusicBrainz)  
   - MusicBrainz client headers  
   - Local paths and settings  

This file centralizes all external configuration and credentials.

---

# **Current Status Summary**

| Component | Status |
|----------|--------|
| Fingerprint extraction | ✔ Fully working (via audiofp-server) |
| Fingerprint → MBID lookup | ❌ Not implemented (blocked by missing AcoustID lookup key) |
| MusicBrainz search | ✔ Working (tested via app_search_music_brainz.py) |
| Tag reading | ✔ Working (separate script, not integrated) |
| Tag rewriting | ⚠ Partial (needs verified metadata) |
| Filename normalization | ⚠ Partial |
| Folder structure mapping | ✔ Implemented |
| Mismatch detection | ❌ Not implemented |
| Full verification pipeline | ❌ Not implemented |
| Database integration | ✔ Implemented |
| Duplicate detection | ✔ Implemented |

---

# AudioFP (Rust Library)

AudioFP is a high‑performance Rust library for audio fingerprinting.  
It implements multiple fingerprinting algorithms (Wang, Panako, Haitsma–Kalker, neural/ONNX, watermark detection) and provides the core DSP engine used by the AudioFP Server.

This repository contains **only the library**, not a server or CLI.  
It is intended to be used as a dependency in other Rust projects.

---

## Repo

Repo found in https://github.com/themankindproject/audiofp

### Clone and install

```
git clone https://github.com/themankindproject/audiofp
cd audiofp
cargo build --release
```


## 📦 Features

- Pure Rust DSP pipeline
- Multiple fingerprinting algorithms
- Optional ONNX neural embedding support
- Optional watermark detection
- `no_std` compatible (DSP‑only mode)
- Fast, safe, modern Rust implementation

---

## 📂 Repository Structure

```
audiofp/
  ├── Cargo.toml
  ├── src/
  │    ├── lib.rs
  │    └── ...
  └── examples/
```

---

## 🔧 Prerequisites

Install Rust:

```
curl [https://sh.rustup.rs](https://sh.rustup.rs) -sSf | sh
```

Verify:

```
rustc --version
cargo --version
```

---

## 🌐 Fixing crates.io download issues (recommended)

Create or edit:

```
~/.cargo/config.toml
```

Add:

```toml
[source.crates-io]
replace-with = "ustc"

[source.ustc]
registry = "https://mirrors.ustc.edu.cn/crates.io-index"

[registries.crates-io]
protocol = "sparse"
```

This improves reliability and speed when downloading dependencies.

---

## 🛠️ Building the Library

Inside the `audiofp` folder:

```
cargo build --release
```

This produces:

```
target/release/libaudiofp.rlib
target/release/libaudiofp.d
```

These are used by other Rust projects (e.g., the AudioFP Server).

---

## 🧪 Running Examples

Some examples require the `std` feature:

```
cargo run --example enroll_file --features std
```

---

## 📄 License

MIT License

---

# AudioFP Server (Rust interface to Library)

A lightweight Rust HTTP server that exposes the **AudioFP** audio‑fingerprinting library through a simple JSON API.  
Designed to be used from Python for automatic tag detection and metadata repair.

---

## 🚀 Features

- Fast Axum 0.7 HTTP server
- Uses the Rust AudioFP library for fingerprinting
- JSON API for:
  - `/api/status`
  - `/api/match`
  - `/api/index`
- Python‑friendly interface

---

## 📦 Requirements

- Rust toolchain
- The AudioFP library cloned next to this repo:

```
YourFolder/
  audiofp/
  Sorter/
    audiofp-server/
```

---

## 🔧 Building

```
cargo build --release
```

Binary output:

```
target/release/audiofp-server
```

---

## ▶️ Running

```
./target/release/audiofp-server
```

Server starts at:

```
[http://127.0.0.1:5000](http://127.0.0.1:5000)
```

---

## 🧪 Testing

Open:

```
http://localhost:5000/api/status
```

Expected:

```json
{"status":"ok"}
```

---

## 📡 API

### `POST /api/match`

```json
{
  "filepath": "/path/to/file.mp3"
}
```

### `POST /api/index`

```json
{
  "directory": "/path/to/music/"
}
```

---

## 🐍 Python Integration

Example:

```python
import requests

resp = requests.post(
    "http://localhost:5000/api/match",
    json={"filepath": "/path/song.mp3"}
)

print(resp.json())
```

---

## 📄 License

MIT License

---

Here is a **clean, structured, installation‑ready section** you can drop directly into your `README.md`.  
It explains the **exact folder layout**, **Rust build steps**, **server build**, and **Python setup** in a way that is reproducible and friendly for anyone reviewing your repo.

Everything below is written to integrate smoothly with the rest of your README.

---

# 🔧 Installation & Setup

This project requires both **Rust** (for the fingerprinting backend) and **Python** (for the organizer and metadata tools).  
Follow the steps below to set up the environment exactly as intended.

---

## 1. Install Rust

Rust is required to build the fingerprinting engine and the audiofp-server.

Install Rust using rustup:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Verify installation:

```bash
rustc --version
cargo --version
```

---

## 2. Create the Required Folder Structure

The project expects the following layout:

```
YourFolder/
  audiofp/
  Sorter/
    audiofp-server/
```

Go to your base Folder
```bash
cd YourFolder
```
**Note: Verify the folder structure is correct after cloning the repositories. Program will not work in a different Layout**

---

## 3. Clone the AudioFP Library

From your base folder:
```bash
cd YourFolder
```

Clone the upstream audiofp repository:

```bash
git clone https://github.com/themankindproject/audiofp.git
```

This provides the Rust fingerprinting library used by the server.

---

## 4. Build the AudioFP Library

Inside the `audiofp` folder:

```bash
cd audiofp
cargo build --release
```

This produces:

```
audiofp/target/release/libaudiofp.a
```

This static library is required by the server.

---

## 5. Clone Sorter and Build the audiofp-server

From your base folder:
```bash
cd YourFolder
```

```bash
git clone https://github.com/fedetony/Sorter.git
cd Sorter
cd audiofp-server
```

Build the server:

```bash
cargo build --release
```

This produces the server binary:

```
audiofp-server/target/release/audiofp-server
```

This binary is the local fingerprinting backend used by the Python tools.

---

## 6. Configure the Project

Copy the configuration template:

```bash
cp config.template.yaml config.yaml
```

Edit `config.yaml` and fill in:

- AcoustID API key  
- MusicBrainz client headers  
- Local paths (audiofp-server path, database path, etc.)

This file centralizes all external configuration.

---

## 7. Install Python Dependencies

Inside the `Sorter/` folder:

```bash
pip install -r requirements.txt
```

This installs:

- Inquirer
- Textual
- Requests   
- and any other required modules  

---

## 8. Running the Components

### Start the fingerprint server:

```bash
./audiofp-server/target/release/audiofp-server
```

### Run the MusicBrainz search tester:

```bash
python app_search_music_brainz.py
```

### Run the fingerprint tester:

```bash
python app_fingerprint_files.py
```

These tools validate that fingerprinting and metadata lookup pipelines are working.

---

# 📦 Installation Summary

| Step | Component | Status |
|------|-----------|--------|
| 1 | Install Rust | Required |
| 2 | Create folder structure | Required |
| 3 | Clone audiofp | Required |
| 4 | Build audiofp | Required |
| 5 | Clone & build audiofp-server | Required |
| 6 | Configure `config.yaml` | Required |
| 7 | Install Python dependencies | Required |
| 8 | Run server + test apps | Recommended |

---

## 💸 Support My Work

If **Sorter** has helped you, consider supporting development:

- **G1 (Junas Cesium):** `D9CFSvUHQDJJ4iFExVU4fTMAidADV8kedabeqtV6o3CS`  
- **BTC (Bitcoin):** `n211bgvuTVfwFoV6xwcHE5pPe4zWuQ27je`  
- Or become a sponsor via [GitHub Sponsors](https://github.com/sponsors/fedetony)

---

<div align="center">

<br><br>

**☕ With Coffee & Love by FG ❤️**

</div>


