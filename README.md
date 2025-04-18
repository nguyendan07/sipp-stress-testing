# SIP VoIP Stress Testing using SIPp

This project provides resources and configuration for performing stress and load testing on SIP/VoIP infrastructure using the SIPp traffic generator. The primary test scenario focuses on simulating User Agent Client (UAC) behavior as defined in `test_scenario/uac_custom.xml`.

## Prerequisites

*   **Ubuntu Linux:** Installation instructions are provided for Ubuntu-based systems.
*   **SIPp:** The core testing tool. (See Installation section below)
*   **Target SIP Server/PBX:** You need a SIP endpoint (IP address and port) to test against.
*   **Basic understanding of SIP:** Familiarity with SIP concepts and call flows is helpful.

## Installation (SIPp on Ubuntu)
If the repository version is outdated or you need specific features (like TLS, PCAP play), you might need to compile from source:

1.  **Install Dependencies:**
    ```bash
    sudo apt update
    sudo apt install build-essential cmake git libssl-dev libpcap-dev libncurses5-dev libnet1-dev # Add libsctp-dev if SCTP support is needed
    ```

2.  **Download Source:** Get the latest stable release from the [SIPp GitHub Releases page](https://github.com/SIPp/sipp/releases).

3.  **Compile and Install:**
    ```bash
    wget https://github.com/SIPp/sipp/releases/download/vX.Y.Z/sipp-X.Y.Z.tar.gz # Replace X.Y.Z with version number
    tar -xzvf sipp-X.Y.Z.tar.gz
    cd sipp-X.Y.Z
    cmake . -DUSE_PCAP=1 -DUSE_SSL=1 -DUSE_SCTP=1
    make
    sudo make install
    ```

Verify the installation:
```bash
sipp -v
```

## Project Structure

```
.
├── audio_files/              # Original audio files (various formats possible)
│   ├── agents/
│   ├── confirm/
│   └── renewal/
│       └── ... (original .wav files)
├── audio_files/converted/    # Audio files converted for SIPp (e.g., PCMU/PCMA)
│   ├── agents/
│   ├── confirm/
│   └── renewal/
│       ├── renewal_0.wav     # Converted audio files referenced by scenarios
│       ├── renewal_1.wav
│       └── ...
├── test_scenario/            # SIPp scenario definitions and data
│   ├── uac_custom.csv        # CSV data file used by uac_custom.xml (e.g., user credentials, numbers)
│   ├── uac_custom.xml        # The primary UAC stress test scenario file
│   └── uac.xml               # Another potential scenario file
└── README.md                 # This file
```

*   **`audio_files/converted/`**: Contains audio files likely converted to a format SIPp can stream via RTP (commonly G.711 μ-law/PCMU or A-law/PCMA, 8kHz, 8-bit mono). These are referenced within the `.xml` scenario files.
*   **`test_scenario/uac_custom.xml`**: This is the core scenario definition file that dictates the SIP messages, call flow, and actions (like playing audio).
*   **`test_scenario/uac_custom.csv`**: This file provides variable data injected into the scenario, allowing multiple different calls to be simulated using the same XML template. Fields are typically referenced in the XML using `[fieldN]`.

## Usage

1.  **Navigate:** Open your terminal in the root directory of this project.
2.  **Configure:**
    *   Edit `test_scenario/uac_custom.csv` to include the necessary data for your test calls (e.g., usernames, passwords, target numbers).
    *   Review `test_scenario/uac_custom.xml` and adjust any static parameters if needed (e.g., source IP if not using `-i`, specific headers).
3.  **Run SIPp:** Execute the `sipp` command, pointing it to your target server and the scenario files.

**Run Command:**

```bash
sipp 118.69.115.150:5060 -sf test_scenario/uac_custom.xml -inf test_scenario/uac_custom.csv -m 1000 -l 150 -r 15 -i 210.245.0.142 -p 5060 -s 19006600 -d 10 -trace_err -trace_stat
```

**Explanation of Common Options:**

*   `118.69.115.150:5060`: **Required.** The IP address and port of the SIP server you are testing.
*   `-sf test_scenario/uac_custom.xml`: **Required.** Specifies the scenario file to use.
*   `-inf test_scenario/uac_custom.csv`: Specifies the data injection file. SIPp will read data line-by-line from this CSV.
*   `-m <NUMBER_OF_CALLS>`: Total number of calls to place.
*   `-l <CONCURRENT_CALL_LIMIT>`: Maximum number of calls active simultaneously.
*   `-r <CALL_RATE>`: Number of new calls to initiate per second.
*   `-i <LOCAL_IP_ADDRESS>`: Sets the source IP address for SIP messages. Important if your machine has multiple interfaces.
*   `-p <LOCAL_PORT>`: Sets the source port for SIP messages.
*   `-d <CALL_DURATION_MS>`: Default duration for calls (can be overridden in the scenario). Often used for pauses within the scenario (`<pause duration="[duration]">`).
*   `-bg`: Run SIPp in background mode (useful for long tests).
*   `-s <SERVICE>`: Sets the service number or username (can often be handled via CSV).
*   `-ap <PASSWORD>`: Sets the authentication password (can often be handled via CSV).
*   `-trace_err`: Dumps errors to a `_errors.log` file.
*   `-trace_stat`: Dumps statistics periodically to a `_stats.csv` file.

## Notes

*   Monitor the performance of both the SIPp client machine and the target SIP server during the test.
*   Consult the official [SIPp Documentation](https://sipp.readthedocs.io/en/latest/) for detailed information on scenario syntax and command-line options.
