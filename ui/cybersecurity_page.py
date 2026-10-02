
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QListWidget,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QScrollArea,
    QSizePolicy,
)

from cybersecurity.lab_manager import LabManager
from cybersecurity.scanner import NmapScanner
from cybersecurity.report_generator import ReportGenerator
from cybersecurity.scan_history import ScanHistory


class ScanWorker(QThread):
    scan_finished = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, scanner, target):
        super().__init__()
        self.scanner = scanner
        self.target = target

    def run(self):
        try:
            result = self.scanner.scan(self.target)

            if not isinstance(result, dict):
                raise RuntimeError("Scanner returned an invalid result.")

            if not result.get("success"):
                self.error_occurred.emit(
                    result.get("error", "The scan failed.")
                )
                return

            self.scan_finished.emit(result)

        except Exception as error:
            self.error_occurred.emit(str(error))


class CybersecurityPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.lab_manager = LabManager()
        self.scanner = NmapScanner(self.lab_manager)
        self.report_generator = ReportGenerator()
        self.scan_history = ScanHistory()

        self.scan_worker = None
        self.current_scan_id = None

        self.create_ui()
        self.refresh_targets()
        self.refresh_history()

    def create_ui(self):
        # The scroll area keeps every control accessible on shorter windows.
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        page_layout.addWidget(scroll)

        content = QWidget()
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(14)
        scroll.setWidget(content)

        title = QLabel("Cybersecurity Lab")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        description = QLabel(
            "Register authorized private or loopback lab targets, "
            "run controlled Nmap scans, and review previous results."
        )
        description.setWordWrap(True)

        main_layout.addWidget(title)
        main_layout.addWidget(description)

        # Target registration
        target_group = QGroupBox("Register Lab Target")
        target_layout = QFormLayout(target_group)
        target_layout.setContentsMargins(14, 18, 14, 14)
        target_layout.setHorizontalSpacing(12)
        target_layout.setVerticalSpacing(10)
        target_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        self.target_input = QLineEdit()
        self.target_input.setMinimumHeight(38)
        self.target_input.setPlaceholderText(
            "Example: 192.168.1.10 or 192.168.1.0/24"
        )

        self.description_input = QLineEdit()
        self.description_input.setMinimumHeight(38)
        self.description_input.setPlaceholderText(
            "Example: Local OWASP Juice Shop lab"
        )

        target_layout.addRow("IP / Network:", self.target_input)
        target_layout.addRow("Description:", self.description_input)

        self.register_button = QPushButton("Register Target")
        self.register_button.setMinimumHeight(40)
        self.register_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.register_button.clicked.connect(self.register_target)
        target_layout.addRow(self.register_button)

        main_layout.addWidget(target_group)

        # Registered targets and scan controls share a row.
        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(14)

        registered_group = QGroupBox("Registered Targets")
        registered_layout = QVBoxLayout(registered_group)
        registered_layout.setContentsMargins(12, 18, 12, 12)
        registered_layout.setSpacing(10)

        self.target_list = QListWidget()
        self.target_list.setMinimumHeight(105)
        self.target_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        registered_layout.addWidget(self.target_list, 1)

        target_actions = QHBoxLayout()
        target_actions.setSpacing(8)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setMinimumHeight(36)
        self.remove_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.remove_button.clicked.connect(self.remove_selected_target)

        self.refresh_targets_button = QPushButton("Refresh")
        self.refresh_targets_button.setMinimumHeight(36)
        self.refresh_targets_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.refresh_targets_button.clicked.connect(self.refresh_targets)

        target_actions.addWidget(self.remove_button)
        target_actions.addWidget(self.refresh_targets_button)
        registered_layout.addLayout(target_actions)

        scan_group = QGroupBox("Scan")
        scan_layout = QVBoxLayout(scan_group)
        scan_layout.setContentsMargins(12, 18, 12, 12)
        scan_layout.setSpacing(9)

        scan_label = QLabel("Target to scan:")
        self.scan_target_input = QLineEdit()
        self.scan_target_input.setMinimumHeight(36)
        self.scan_target_input.setPlaceholderText(
            "Enter a registered IP or network"
        )

        self.scan_button = QPushButton("Run Nmap Scan")
        self.scan_button.setMinimumHeight(38)
        self.scan_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.scan_button.clicked.connect(self.confirm_and_scan)

        self.scan_status = QLabel("Scanner is ready.")
        self.scan_status.setWordWrap(True)
        self.scan_status.setMinimumHeight(24)

        scan_layout.addWidget(scan_label)
        scan_layout.addWidget(self.scan_target_input)
        scan_layout.addWidget(self.scan_button)
        scan_layout.addWidget(self.scan_status)
        scan_layout.addStretch(1)

        upper_layout.addWidget(registered_group, 1)
        upper_layout.addWidget(scan_group, 1)
        main_layout.addLayout(upper_layout)

        # Results
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(12, 18, 12, 12)

        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setMinimumHeight(115)
        self.results_output.setPlaceholderText(
            "Scan results and report paths will appear here."
        )
        results_layout.addWidget(self.results_output)
        main_layout.addWidget(results_group)

        # History
        history_group = QGroupBox("Scan History")
        history_layout = QVBoxLayout(history_group)
        history_layout.setContentsMargins(12, 18, 12, 12)
        history_layout.setSpacing(10)

        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(110)
        self.history_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.history_list.itemDoubleClicked.connect(
            self.open_selected_report
        )
        history_layout.addWidget(self.history_list, 1)

        history_actions = QHBoxLayout()
        history_actions.setSpacing(8)

        self.history_refresh_button = QPushButton("Refresh History")
        self.history_refresh_button.setMinimumHeight(36)
        self.history_refresh_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.history_refresh_button.clicked.connect(self.refresh_history)

        self.open_report_button = QPushButton("Open Report")
        self.open_report_button.setMinimumHeight(36)
        self.open_report_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.open_report_button.clicked.connect(self.open_selected_report)

        history_actions.addWidget(self.history_refresh_button)
        history_actions.addWidget(self.open_report_button)
        history_layout.addLayout(history_actions)

        main_layout.addWidget(history_group)
        main_layout.addStretch(1)

    # --------------------------------------------------
    # Target management
    # --------------------------------------------------

    def register_target(self):
        target = self.target_input.text().strip()
        description = self.description_input.text().strip()

        if not target:
            QMessageBox.warning(
                self,
                "Missing Target",
                "Enter an IP address or network.",
            )
            return

        try:
            result = self.lab_manager.add_target(
                target,
                description,
            )

            # Support both string and dictionary results.
            if isinstance(result, dict):
                if not result.get("success"):
                    raise ValueError(
                        result.get(
                            "error",
                            "Registration failed.",
                        )
                    )

                registered_target = result.get(
                    "target",
                    target,
                )
            else:
                registered_target = str(result)

            self.target_input.clear()
            self.description_input.clear()
            self.refresh_targets()

            QMessageBox.information(
                self,
                "Target Registered",
                f"Registered target: {registered_target}",
            )

        except Exception as error:
            QMessageBox.warning(
                self,
                "Registration Failed",
                str(error),
            )

    def refresh_targets(self):
        self.target_list.clear()

        try:
            details_method = getattr(
                self.lab_manager,
                "list_target_details",
                None,
            )

            if callable(details_method):
                targets = details_method()

                for item in targets:
                    target = item["target"]
                    description = item.get(
                        "description",
                        "",
                    )

                    label = target

                    if description:
                        label += f" — {description}"

                    self.target_list.addItem(label)

            else:
                for item in self.lab_manager.list_targets():
                    if isinstance(item, dict):
                        target = item.get("target", "")
                        description = item.get(
                            "description",
                            "",
                        )
                    else:
                        target = str(item)
                        description = ""

                    label = target

                    if description:
                        label += f" — {description}"

                    self.target_list.addItem(label)

        except Exception as error:
            self.scan_status.setText(
                f"Could not load targets: {error}"
            )

    def remove_selected_target(self):
        selected = self.target_list.currentItem()

        if selected is None:
            QMessageBox.information(
                self,
                "No Selection",
                "Select a registered target first.",
            )
            return

        target = selected.text().split(" — ", 1)[0]

        confirm = QMessageBox.question(
            self,
            "Remove Target",
            f"Remove {target} from the registered lab scope?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            removed = self.lab_manager.remove_target(target)

            if isinstance(removed, dict):
                removed = removed.get("success", False)

            if removed:
                self.refresh_targets()
                self.scan_status.setText(
                    f"Removed {target} from lab scope."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Removal Failed",
                    "The target was not found.",
                )

        except Exception as error:
            QMessageBox.warning(
                self,
                "Removal Failed",
                str(error),
            )

    # --------------------------------------------------
    # Scan workflow
    # --------------------------------------------------

    def confirm_and_scan(self):
        target = self.scan_target_input.text().strip()

        if not target:
            QMessageBox.warning(
                self,
                "Missing Target",
                "Enter a registered target to scan.",
            )
            return

        if not self.lab_manager.is_authorized(target):
            QMessageBox.warning(
                self,
                "Target Not Registered",
                "Register this target in the lab scope first.",
            )
            return

        if (
            self.scan_worker is not None
            and self.scan_worker.isRunning()
        ):
            QMessageBox.information(
                self,
                "Scan Running",
                "Wait for the current scan to finish.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirm Nmap Scan",
            (
                "Run a TCP connect and service detection scan "
                f"against:\n\n{target}\n\n"
                "This scans the top 100 ports. Continue only "
                "if you own or are authorized to test this target."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.current_scan_id = (
                self.scan_history.start_scan(target)
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "History Error",
                f"Could not record the scan: {error}",
            )
            return

        self.scan_button.setEnabled(False)
        self.register_button.setEnabled(False)
        self.remove_button.setEnabled(False)

        self.scan_status.setText(
            "Nmap scan is running..."
        )
        self.results_output.clear()

        self.refresh_history()

        self.scan_worker = ScanWorker(
            self.scanner,
            target,
        )

        self.scan_worker.scan_finished.connect(
            self.handle_scan_finished
        )
        self.scan_worker.error_occurred.connect(
            self.handle_scan_error
        )
        self.scan_worker.finished.connect(
            self.scan_worker_finished
        )

        self.scan_worker.start()

    def handle_scan_finished(self, result):
        scan_id = self.current_scan_id

        try:
            report_result = (
                self.report_generator.save_report(result)
            )

            if not report_result.get("success"):
                raise RuntimeError(
                    "Scan completed, but report generation failed: "
                    + report_result.get(
                        "error",
                        "Unknown error",
                    )
                )

            parsed = self.report_generator.parse_nmap_xml(
                result.get("xml", "")
            )

            lines = [
                f"Target: {result.get('target', '')}",
                "",
            ]

            if parsed.get("success"):
                hosts = parsed.get("hosts", [])

                if not hosts:
                    lines.append(
                        "No hosts were returned."
                    )

                for host in hosts:
                    addresses = ", ".join(
                        address["address"]
                        for address in host.get(
                            "addresses",
                            [],
                        )
                    ) or "Unknown"

                    lines.extend([
                        f"Host: {addresses}",
                        f"Status: {host.get('status', 'Unknown')}",
                    ])

                    if host.get("hostnames"):
                        lines.append(
                            "Hostnames: "
                            + ", ".join(
                                host["hostnames"]
                            )
                        )

                    if not host.get("ports"):
                        lines.append(
                            "No port details returned."
                        )

                    for port in host.get("ports", []):
                        service = " ".join(
                            value
                            for value in (
                                port.get("service", ""),
                                port.get("product", ""),
                                port.get("version", ""),
                            )
                            if value
                        )

                        lines.append(
                            f"  {port.get('protocol', '')}/"
                            f"{port.get('port', '')} "
                            f"{port.get('state', '')} "
                            f"{service}".rstrip()
                        )

                    lines.append("")

            else:
                lines.append(
                    "Could not parse scan results: "
                    + parsed.get(
                        "error",
                        "Unknown error",
                    )
                )

            json_path = report_result.get(
                "json_path",
                "",
            )
            text_path = report_result.get(
                "text_path",
                "",
            )

            summary = "\n".join(lines)

            self.scan_history.complete_scan(
                scan_id,
                summary=summary,
                json_report=json_path,
                text_report=text_path,
            )

            lines.extend([
                "",
                "Reports saved:",
                f"JSON: {json_path}",
                f"Text: {text_path}",
            ])

            self.results_output.setPlainText(
                "\n".join(lines)
            )

            self.scan_status.setText(
                "Scan completed successfully."
            )

        except Exception as error:
            if scan_id is not None:
                try:
                    self.scan_history.fail_scan(
                        scan_id,
                        str(error),
                    )
                except Exception:
                    pass

            self.scan_status.setText(
                "Scan completed, but saving the result failed."
            )
            self.results_output.setPlainText(
                str(error)
            )

        finally:
            self.refresh_history()

    def handle_scan_error(self, error):
        if self.current_scan_id is not None:
            try:
                self.scan_history.fail_scan(
                    self.current_scan_id,
                    error,
                )
            except Exception:
                pass

        self.scan_status.setText(
            "Scan encountered an error."
        )
        self.results_output.setPlainText(
            str(error)
        )
        self.refresh_history()

    def scan_worker_finished(self):
        self.scan_button.setEnabled(True)
        self.register_button.setEnabled(True)
        self.remove_button.setEnabled(True)

        self.scan_worker = None
        self.current_scan_id = None

    # --------------------------------------------------
    # Scan history
    # --------------------------------------------------

    def refresh_history(self):
        self.history_list.clear()

        try:
            scans = self.scan_history.list_scans(
                limit=100
            )

            for scan in scans:
                scan_id = scan.get("id")
                target = scan.get(
                    "target",
                    "Unknown target",
                )
                status = scan.get(
                    "status",
                    "unknown",
                )
                started = scan.get(
                    "started_at",
                    "",
                )

                label = (
                    f"#{scan_id} | {target} | "
                    f"{status.upper()} | {started}"
                )

                self.history_list.addItem(label)

        except Exception as error:
            self.scan_status.setText(
                f"Could not load scan history: {error}"
            )

    def open_selected_report(self, item=None):
        selected = item or self.history_list.currentItem()

        if selected is None:
            QMessageBox.information(
                self,
                "No Scan Selected",
                "Select a scan from the history first.",
            )
            return

        try:
            scan_id = int(
                selected.text()
                .split("|", 1)[0]
                .replace("#", "")
                .strip()
            )

            scan = self.scan_history.get_scan(
                scan_id
            )

            if not scan:
                QMessageBox.warning(
                    self,
                    "Scan Not Found",
                    "This scan record no longer exists.",
                )
                return

            # Prefer the text report for easy viewing.
            report_path = (
                scan.get("text_report")
                or scan.get("json_report")
            )

            if not report_path:
                QMessageBox.information(
                    self,
                    "No Report",
                    "This scan does not have a saved report.",
                )
                return

            path = Path(report_path)

            if not path.is_file():
                QMessageBox.warning(
                    self,
                    "Report Missing",
                    f"The report file could not be found:\n{path}",
                )
                return

            opened = QDesktopServices.openUrl(
                QUrl.fromLocalFile(
                    str(path.resolve())
                )
            )

            if not opened:
                QMessageBox.warning(
                    self,
                    "Open Failed",
                    "The report could not be opened.",
                )

        except Exception as error:
            QMessageBox.warning(
                self,
                "Open Report Failed",
                str(error),
            )