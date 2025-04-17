#!/usr/bin/env python3
"""
SIPp RTP Port Checker
---------------------
Tool to extract RTP port information from SIPp scenario files
"""

import os
import sys
import re
import xml.etree.ElementTree as ET
import argparse


def extract_rtp_ports_from_xml(xml_file):
    """
    Extract RTP port information from a SIPp XML scenario file
    """
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        rtp_ports = {}
        variables = {}
        
        # Look for global variables
        for elem in root.findall("./Global//*[@name][@value]"):
            if 'name' in elem.attrib and 'value' in elem.attrib:
                name = elem.attrib['name']
                value = elem.attrib['value']
                variables[name] = value
                if 'port' in name.lower() and 'sip' not in name.lower():
                    print(f"Potential RTP variable: {name} = {value}")
        
        # Look for SDP content in send messages
        sdp_pattern = re.compile(r'm=audio\s+(\d+|(\[\w+\]))')
        media_port_pattern = re.compile(r'\[media_port\]')
        auto_media_port_pattern = re.compile(r'\[auto_media_port\]')
        
        for send_elem in root.findall(".//send"):
            if send_elem.text:
                sdp_matches = sdp_pattern.findall(send_elem.text)
                if sdp_matches:
                    for match in sdp_matches:
                        port = match[0]
                        if port.isdigit():
                            rtp_ports['explicit'] = port
                            print(f"Found explicit RTP port: {port}")
                        else:
                            print(f"Found variable RTP port reference: {port}")
                            if port == '[media_port]' and 'media_port' in variables:
                                rtp_ports['media_port'] = variables['media_port']
                
                # Check for media_port variable
                if media_port_pattern.search(send_elem.text):
                    rtp_ports['uses_media_port'] = True
                
                # Check for auto_media_port variable
                if auto_media_port_pattern.search(send_elem.text):
                    rtp_ports['uses_auto_media_port'] = True
        
        # Look for media tags
        for media_elem in root.findall(".//nop[@action='rtp_stream']"):
            if 'args' in media_elem.attrib:
                args = media_elem.attrib['args']
                port_match = re.search(r'port=(\d+)', args)
                if port_match:
                    port = port_match.group(1)
                    rtp_ports['rtp_stream'] = port
                    print(f"Found RTP stream port: {port}")
        
        return rtp_ports, variables
        
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return {}, {}
    except Exception as e:
        print(f"Error processing {xml_file}: {str(e)}")
        return {}, {}


def scan_pcap_for_rtp(pcap_file):
    """
    Scan a PCAP file to detect RTP traffic and ports used
    Requires the tshark command-line tool
    """
    try:
        import subprocess
        
        print(f"\nScanning PCAP file: {pcap_file}")
        
        # Check if tshark is installed
        try:
            subprocess.run(['tshark', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            print("tshark not found. Please install Wireshark/tshark to use this feature.")
            return {}
        
        # Run tshark to extract RTP info
        cmd = ['tshark', '-r', pcap_file, '-Y', 'rtp', '-T', 'fields', '-e', 'udp.srcport', '-e', 'udp.dstport']
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"Error running tshark: {result.stderr}")
            return {}
        
        # Process results
        src_ports = set()
        dst_ports = set()
        
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    src_ports.add(parts[0])
                    dst_ports.add(parts[1])
        
        if src_ports or dst_ports:
            print("Found RTP ports in PCAP:")
            print(f"  Source ports: {', '.join(sorted(src_ports))}")
            print(f"  Destination ports: {', '.join(sorted(dst_ports))}")
            return {'src_ports': list(src_ports), 'dst_ports': list(dst_ports)}
        else:
            print("No RTP traffic found in the PCAP file.")
            return {}
            
    except Exception as e:
        print(f"Error scanning PCAP: {str(e)}")
        return {}


def check_sipp_commandline(scenario_file):
    """
    Try to find SIPp command line arguments in the directory
    """
    try:
        directory = os.path.dirname(scenario_file)
        if not directory:
            directory = '.'
            
        print(f"\nLooking for SIPp command lines in {directory}...")
        
        # Common script file extensions
        extensions = ['.sh', '.bash', '.cmd', '.bat', '.txt']
        rtp_port_info = {}
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Check if it's a potential script file
            is_script = any(filename.endswith(ext) for ext in extensions)
            is_text = os.path.isfile(file_path) and not filename.endswith(('.pcap', '.xml', '.csv', '.wav'))
            
            if is_script or is_text:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Look for sipp command
                        if 'sipp' in content:
                            print(f"Potential SIPp script found: {filename}")
                            
                            # Look for media port arguments
                            mp_match = re.search(r'-mp\s+(\d+)', content)
                            if mp_match:
                                rtp_port_info['media_port'] = mp_match.group(1)
                                print(f"  Media port (-mp): {mp_match.group(1)}")
                            
                            # Look for min/max RTP port arguments
                            min_match = re.search(r'-min_rtp_port\s+(\d+)', content)
                            max_match = re.search(r'-max_rtp_port\s+(\d+)', content)
                            
                            if min_match:
                                rtp_port_info['min_rtp_port'] = min_match.group(1)
                                print(f"  Min RTP port: {min_match.group(1)}")
                            
                            if max_match:
                                rtp_port_info['max_rtp_port'] = max_match.group(1)
                                print(f"  Max RTP port: {max_match.group(1)}")
                except Exception:
                    # Skip files that can't be read as text
                    pass
                    
        return rtp_port_info
        
    except Exception as e:
        print(f"Error checking SIPp command lines: {str(e)}")
        return {}


def analyze_directory(directory):
    """
    Analyze all XML and PCAP files in a directory
    """
    xml_files = []
    pcap_files = []
    
    # Find all XML and PCAP files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.xml'):
                xml_files.append(os.path.join(root, file))
            elif file.lower().endswith('.pcap'):
                pcap_files.append(os.path.join(root, file))
    
    print(f"Found {len(xml_files)} XML files and {len(pcap_files)} PCAP files")
    
    # Process XML files
    for xml_file in xml_files:
        print(f"\nAnalyzing SIPp scenario: {xml_file}")
        rtp_ports, variables = extract_rtp_ports_from_xml(xml_file)
        
        if rtp_ports:
            check_sipp_commandline(xml_file)
    
    # Process PCAP files (optional)
    for pcap_file in pcap_files[:3]:  # Limit to first 3 to avoid lengthy processing
        scan_pcap_for_rtp(pcap_file)


def main():
    parser = argparse.ArgumentParser(description='Extract RTP port information from SIPp scenario files')
    
    parser.add_argument('-f', '--file', help='SIPp XML scenario file to analyze')
    parser.add_argument('-d', '--directory', help='Directory containing SIPp scenarios to analyze')
    parser.add_argument('-p', '--pcap', help='PCAP file to scan for RTP traffic')
    
    args = parser.parse_args()
    
    if args.file:
        print(f"Analyzing SIPp scenario: {args.file}")
        rtp_ports, variables = extract_rtp_ports_from_xml(args.file)
        
        if rtp_ports:
            check_sipp_commandline(args.file)
            
    elif args.directory:
        analyze_directory(args.directory)
        
    elif args.pcap:
        scan_pcap_for_rtp(args.pcap)
        
    else:
        parser.print_help()
        print("\nNo input specified. Please provide a file, directory, or PCAP to analyze.")


if __name__ == "__main__":
    main()
