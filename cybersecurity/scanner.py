import ipaddress
import shutil
import subprocess
import xml.etree.ElementTree as ET


class NmapScanner:
    def __init__(self, lab_manager, timeout=120):
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("Timeout must be a positive number.")

        self.lab_manager = lab_manager
        self.timeout = timeout

    def scan(self, target):
        target = str(target).strip()

        # Validate and normalize the target.
        try:
            network = ipaddress.ip_network(target, strict=False)
        except ValueError as error:
            return {
                "success": False,
                "target": target,
                "error": f"Invalid target: {error}",
            }

        normalized_target = str(network)

        # Restrict scan scope.
        if network.version == 4 and network.prefixlen < 24:
            return {
                "success": False,
                "target": normalized_target,
                "error": "IPv4 scan scope cannot exceed /24.",
            }

        if network.version == 6 and network.prefixlen < 120:
            return {
                "success": False,
                "target": normalized_target,
                "error": "IPv6 scan scope cannot exceed /120.",
            }

        # Check authorization.
        if not self.lab_manager.is_authorized(normalized_target):
            return {
                "success": False,
                "target": normalized_target,
                "error": (
                    "Target is not registered in the "
                    "authorized lab scope."
                ),
            }

        # Locate Nmap.
        nmap_path = shutil.which("nmap")

        if not nmap_path:
            return {
                "success": False,
                "target": normalized_target,
                "error": (
                    "Nmap was not found. Install Nmap and "
                    "ensure it is available in PATH."
                ),
            }

        # Build a controlled Nmap command.
        command = [
            nmap_path,
            "-sT",
            "-sV",
            "--top-ports",
            "100",
            "-oX",
            "-",
            normalized_target,
        ]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                shell=False,
            )

            if completed.returncode != 0:
                return {
                    "success": False,
                    "target": normalized_target,
                    "error": (
                        completed.stderr.strip()
                        or "Nmap scan failed."
                    ),
                    "returncode": completed.returncode,
                }

            xml_output = completed.stdout.strip()

            if not xml_output:
                return {
                    "success": False,
                    "target": normalized_target,
                    "error": "Nmap returned empty XML output.",
                }

            # Ensure the XML output can be parsed.
            try:
                ET.fromstring(xml_output)
            except ET.ParseError as error:
                return {
                    "success": False,
                    "target": normalized_target,
                    "error": f"Invalid Nmap XML output: {error}",
                }

            return {
                "success": True,
                "target": normalized_target,
                "command": command[1:],
                "xml": xml_output,
                "stderr": completed.stderr.strip(),
                "returncode": completed.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "target": normalized_target,
                "error": (
                    f"Nmap scan exceeded the "
                    f"{self.timeout}-second timeout."
                ),
            }

        except OSError as error:
            return {
                "success": False,
                "target": normalized_target,
                "error": f"Unable to execute Nmap: {error}",
            }
