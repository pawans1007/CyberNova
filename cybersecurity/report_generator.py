import json
import re
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree


class ReportGenerator:
    def __init__(self, reports_dir=None):
        if reports_dir is None:
            reports_dir = (
                Path(__file__).resolve().parent.parent
                / "reports"
            )

        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def parse_nmap_xml(self, xml_data):
        if not isinstance(xml_data, str) or not xml_data.strip():
            return {
                "success": False,
                "error": "Nmap XML data is empty.",
            }

        try:
            root = ElementTree.fromstring(xml_data)
        except ElementTree.ParseError as error:
            return {
                "success": False,
                "error": f"Invalid Nmap XML: {error}",
            }

        if root.tag != "nmaprun":
            return {
                "success": False,
                "error": "Invalid Nmap XML: unexpected root element.",
            }

        hosts = []

        for host in root.findall("host"):
            addresses = []

            for address in host.findall("address"):
                addresses.append({
                    "address": address.get("addr", ""),
                    "type": address.get("addrtype", ""),
                })

            status_element = host.find("status")
            status = (
                status_element.get("state", "unknown")
                if status_element is not None
                else "unknown"
            )

            hostnames = [
                item.get("name", "")
                for item in host.findall(
                    "./hostnames/hostname"
                )
            ]

            ports = []

            for port in host.findall("./ports/port"):
                state_element = port.find("state")
                service_element = port.find("service")

                ports.append({
                    "protocol": port.get("protocol", ""),
                    "port": port.get("portid", ""),
                    "state": (
                        state_element.get("state", "unknown")
                        if state_element is not None
                        else "unknown"
                    ),
                    "service": (
                        service_element.get("name", "")
                        if service_element is not None
                        else ""
                    ),
                    "product": (
                        service_element.get("product", "")
                        if service_element is not None
                        else ""
                    ),
                    "version": (
                        service_element.get("version", "")
                        if service_element is not None
                        else ""
                    ),
                })

            hosts.append({
                "addresses": addresses,
                "hostnames": hostnames,
                "status": status,
                "ports": ports,
            })

        return {
            "success": True,
            "hosts": hosts,
        }

    def _build_text_report(self, report):
        lines = [
            "CyberNova Nmap Scan Report",
            "=" * 32,
            f"Target: {report['target']}",
            f"Created: {report['created_at']}",
            f"Hosts found: {len(report['hosts'])}",
            "",
        ]

        if not report["hosts"]:
            lines.append("No hosts were returned by the scan.")

        for host in report["hosts"]:
            host_addresses = ", ".join(
                item["address"]
                for item in host["addresses"]
            ) or "Unknown"

            lines.extend([
                f"Host: {host_addresses}",
                f"Status: {host['status']}",
            ])

            if host["hostnames"]:
                lines.append(
                    "Names: "
                    + ", ".join(host["hostnames"])
                )

            if not host["ports"]:
                lines.append("No port details returned.")

            for port in host["ports"]:
                service = " ".join(
                    part for part in (
                        port["service"],
                        port["product"],
                        port["version"],
                    )
                    if part
                )

                port_line = (
                    f"  {port['protocol']}/{port['port']} "
                    f"{port['state']}"
                )

                if service:
                    port_line += f" {service}"

                lines.append(port_line)

            lines.append("")

        return "\n".join(lines)

    def save_report(self, scan_result):
        if not isinstance(scan_result, dict):
            return {
                "success": False,
                "error": "Invalid scan result.",
            }

        if not scan_result.get("success"):
            return {
                "success": False,
                "error": "Cannot save an unsuccessful scan.",
            }

        parsed = self.parse_nmap_xml(
            scan_result.get("xml", "")
        )

        if not parsed.get("success"):
            return parsed

        created_at = datetime.now().astimezone()
        timestamp = created_at.strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        target = str(scan_result.get("target", "target"))

        safe_target = re.sub(
            r"[^a-zA-Z0-9_.-]",
            "_",
            target,
        ).strip("._") or "target"

        filename = f"nmap_{safe_target}_{timestamp}"

        report = {
            "created_at": created_at.isoformat(),
            "target": target,
            "hosts": parsed["hosts"],
        }

        json_path = self.reports_dir / f"{filename}.json"
        text_path = self.reports_dir / f"{filename}.txt"

        json_temp = self.reports_dir / f"{filename}.json.tmp"
        text_temp = self.reports_dir / f"{filename}.txt.tmp"

        try:
            json_content = json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            )

            text_content = self._build_text_report(report)

            # Write temporary files first.
            json_temp.write_text(
                json_content,
                encoding="utf-8",
            )

            text_temp.write_text(
                text_content,
                encoding="utf-8",
            )

            # Move completed files into their final locations.
            json_temp.replace(json_path)
            text_temp.replace(text_path)

            return {
                "success": True,
                "json_path": str(json_path),
                "text_path": str(text_path),
                "report": report,
            }

        except OSError as error:
            for temp_path in (json_temp, text_temp):
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

            return {
                "success": False,
                "error": f"Unable to save report: {error}",
            }
