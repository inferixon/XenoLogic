# LogikkQuiz - Logic Quiz Educational Module
# Norwegian logic quiz based on Wojnarowski test style

"""
Logic quiz module for UTILON educational system.
Features:
- 10 logic operation types (modus ponens, modus tollens, etc.)
- 3 answer options per question (different from MatteQuiz 4)
- 3 difficulty levels (based on distractor quality)
- Progress indicator
- Stats tracking
- ADHD-friendly single-window flow
"""

import sys
import random
import os
import json
import time
from datetime import datetime
from typing import Any, Optional
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                                 QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy)
from PySide6.QtGui import QPixmap, QFont, QIcon, QKeyEvent, QColor
from PySide6.QtCore import Qt, QSize, QTimer

# Import UI components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.ui_components import (
    PlayButton,
    ServiceButtonsToolbar,
    SettingControl,
    ResetButton,
    SaveCloseButton,
    BaseQuizWidget,
    SettingsTitleLabel,
    StatusBar,
    create_font_px,
)
from core.ui_config import UI_CONFIG
from core.time_utils import format_compact_timestamp
from core import stats_utils
from core.error_log import log_error_event

# Version
VERSION = '0.1.0'

# Font constant (loaded in class)
FONT_NAME = "Palatino Linotype"

# Human-readable names for operation types (Norwegian)
OPERATION_NAMES = {
    "modus_ponens": "Hvis-så slutning",
    "modus_tollens": "Omvendt hvis-så",
    "universal_instantiation": "Fra alle til én",
    "disjunctive_syllogism": "Enten-eller slutning",
    "hypothetical_syllogism": "Kjede-slutning",
    "contraposition": "Kontraposisjon",
    "existential_instantiation": "Noen finnes",
    "negation_introduction": "Motbevis",
    "insufficient_info": "Ikke nok info",
    "conjunction": "Og-slutning",
    "disjunction_incl": "Eller (begge mulig)",
    "disjunction_excl": "Enten-eller (kun én)",
    "double_negation": "Dobbel nekting",
    "quantifier_all": "Alle",
    "quantifier_none": "Ingen",
    "exception": "Unntak",
    "exception_heuristic": "Unntak (språk)" ,
    "incompatibility": "Uforenlig",
    "class_membership": "Tilhører klasse",
    "subclass": "Underklasse",
    "affirming_consequent_trap": "Felle: bekrefte følgen",
    "denying_antecedent_trap": "Felle: nekte årsaken",
    "biconditional": "Hvis og bare hvis",
    "conjunction_intro": "Sette sammen",
    "addition": "Legge til",
    "simplification": "Forenkle",
    "constructive_dilemma": "Konstruktivt dilemma",
    "absorption": "Absorpsjon",
    "de_morgan": "De Morgans lov",
    "temporal_always": "Alltid",
    "temporal_sometimes": "Noen ganger",
    "contradiction": "Selvmotsigelse",
    "possibility_implication": "Mulighet og følge",
    "excluded_middle": "Enten sant eller usant",
}

LOGIKKQUIZ_STATS_TEMPLATE = {
    "total_sessions": 0,
    "total_questions": 0,
    "correct_answers": 0,
    "last_played": None,
    "best_session_seconds": None,
}


# ============ Accuracy Chart Widget ============

class AccuracyChartWidget(QWidget):
    """Chart widget showing accuracy % or TPO over days. Uses ui_config stats_modal.chart."""

    def __init__(self, chart_config: dict, parent=None):
        super().__init__(parent)
        self.chart_config = chart_config or {}
        self.data_points: list = []  # [{date: str, accuracy: float}, ...]
        self._mode = "accuracy"  # "accuracy" or "tpo"
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        # Chart colors from config
        self.line_color = QColor(self.chart_config.get('line_color', '#007FFF'))
        self.fill_color = QColor(self.chart_config.get('fill_color', '#b3cfff'))
        self.fill_alpha = int(self.chart_config.get('fill_alpha', 100))
        self.axis_color = QColor(self.chart_config.get('axis_color', '#1F2A37'))
        self.grid_color = QColor(self.chart_config.get('grid_color', '#E5E7EB'))
        self.bg_color = QColor(self.chart_config.get('background', '#FFFFFF'))
        self.marker_color = QColor(self.chart_config.get('marker_color', '#1F2A37'))
        self.marker_fill_color = QColor(self.chart_config.get('marker_fill_color', '#007FFF'))
        self.corner_radius = int(self.chart_config.get('corner_radius', 16))
        self.line_width = int(self.chart_config.get('line_width', 2))
        self.marker_radius = int(self.chart_config.get('marker_radius', 4))

    def set_data(self, points: list, mode: str = "accuracy") -> None:
        self.data_points = points  # All time
        self._mode = mode
        self.update()

    def paintEvent(self, event) -> None:
        from PySide6.QtGui import QPainter, QPen, QBrush, QPainterPath
        from PySide6.QtCore import QPointF, QRectF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        margin_left = 50
        margin_right = 20
        margin_top = 20
        margin_bottom = 40
        chart_rect = QRectF(margin_left, margin_top,
                           rect.width() - margin_left - margin_right,
                           rect.height() - margin_top - margin_bottom)

        # Draw background with rounded corners
        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(rect), self.corner_radius, self.corner_radius)
        painter.fillPath(bg_path, QBrush(self.bg_color))

        if not self.data_points or len(self.data_points) < 2:
            painter.setPen(QPen(self.axis_color))
            font = create_font_px('Palatino Linotype', 18)
            painter.setFont(font)
            painter.drawText(chart_rect, Qt.AlignmentFlag.AlignCenter, "Ikke nok data for graf")
            return

        # Calculate bounds based on mode
        if self._mode == "tpo":
            max_tpo = max(dp.get('accuracy', 0) for dp in self.data_points)
            max_val = max(60, ((max_tpo // 30) + 1) * 30)
            min_val = 0
            unit_suffix = "s"
        else:
            min_val = 0
            max_val = 100
            unit_suffix = "%"

        # Draw grid lines
        painter.setPen(QPen(self.grid_color, 1))
        num_grid_lines = 4
        for i in range(num_grid_lines + 1):
            y = chart_rect.top() + (chart_rect.height() * i / num_grid_lines)
            painter.drawLine(QPointF(chart_rect.left(), y), QPointF(chart_rect.right(), y))

        # Draw Y-axis labels
        painter.setPen(QPen(self.axis_color))
        font = create_font_px('Palatino Linotype', 14)
        painter.setFont(font)
        for i in range(num_grid_lines + 1):
            y = chart_rect.top() + (chart_rect.height() * i / num_grid_lines)
            value = int(max_val - (max_val * i / num_grid_lines))
            painter.drawText(QRectF(0, y - 10, margin_left - 5, 20),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{value}{unit_suffix}")

        # Calculate X positions
        num_points = len(self.data_points)
        x_step = chart_rect.width() / (num_points - 1) if num_points > 1 else chart_rect.width()

        # Build points
        points: list = []
        for i, dp in enumerate(self.data_points):
            x = chart_rect.left() + i * x_step
            acc = dp.get('accuracy', 0)
            y = chart_rect.bottom() - (acc / max_val) * chart_rect.height()
            points.append(QPointF(x, y))

        if points:
            # Fill area under line
            fill_path = QPainterPath()
            fill_path.moveTo(QPointF(points[0].x(), chart_rect.bottom()))
            for p in points:
                fill_path.lineTo(p)
            fill_path.lineTo(QPointF(points[-1].x(), chart_rect.bottom()))
            fill_path.closeSubpath()
            fill_color = QColor(self.fill_color)
            fill_color.setAlpha(self.fill_alpha)
            painter.fillPath(fill_path, QBrush(fill_color))

            # Draw line
            line_path = QPainterPath()
            line_path.moveTo(points[0])
            for p in points[1:]:
                line_path.lineTo(p)
            painter.setPen(QPen(self.line_color, self.line_width))
            painter.drawPath(line_path)

            # Draw markers
            painter.setPen(QPen(self.marker_color))
            painter.setBrush(QBrush(self.marker_fill_color))
            for p in points:
                painter.drawEllipse(p, self.marker_radius, self.marker_radius)

        # X-axis labels (dates)
        painter.setPen(QPen(self.axis_color))
        date_font = create_font_px("Palatino Linotype", 12)
        painter.setFont(date_font)

        from core.time_utils import compute_time_axis_ticks

        date_strings = [dp.get('date', '') for dp in self.data_points]
        for i, label in compute_time_axis_ticks(date_strings, max_labels=12):
            x = chart_rect.left() + i * x_step
            painter.drawText(
                QRectF(x - 20, chart_rect.bottom() + 5, 40, 20),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )


# ============ Stats Modal ============

class LogikkQuizStatsModal(QWidget):
    """Stats modal for LogikkQuiz with left metrics, right accuracy chart."""

    def __init__(self, stats_config: dict, ui_config: dict, parent=None):
        super().__init__(parent)
        self.stats_config = stats_config or {}
        self.ui_config = ui_config or {}
        self.left_value_labels: dict = {}

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        settings_cfg = (self.ui_config.get('containers', {}) or {}).get('settings', {})
        settings_colors = settings_cfg.get('colors', {}) if isinstance(settings_cfg, dict) else {}
        self.base_text_color = settings_colors.get('text', '#2C3E50')

        left_cfg = self.stats_config.get('left_table', {})
        left_colors = left_cfg.get('colors', {}) if isinstance(left_cfg, dict) else {}
        self.muted_color = left_colors.get('muted', '#A0AEC0')

        self._build_layout()

    def _build_layout(self) -> None:
        from PySide6.QtWidgets import QGridLayout, QSpacerItem
        from core.ui_components import SettingsTitleLabel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # Title
        title_cfg = self.stats_config.get('title', {})
        title_text = title_cfg.get('text', "STATISTIKK")
        title_label = SettingsTitleLabel(self.ui_config, self)
        title_label.setText(title_text)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Columns
        columns_cfg = self.stats_config.get('columns', {})
        columns_layout = QHBoxLayout()
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(columns_cfg.get('spacing', 60))
        columns_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === LEFT COLUMN (40%) - Metrics ===
        left_container = QWidget()
        left_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        left_container.setStyleSheet("background: transparent; border: none;")
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_table_cfg = self.stats_config.get('left_table', {})
        fonts_cfg = left_table_cfg.get('fonts', {})
        label_font = self._build_font(fonts_cfg.get('label', {}), default_size=26, default_weight='bold')
        value_font = self._build_font(fonts_cfg.get('value', {}), default_size=26, default_weight='bold')

        metrics_grid = QGridLayout()
        metrics_grid.setContentsMargins(0, 0, 0, 0)
        metrics_grid.setHorizontalSpacing(20)
        metrics_grid.setVerticalSpacing(left_table_cfg.get('row_spacing', 12))

        row = 0
        self._add_metric_row(metrics_grid, row, "Totalt økter", "total_sessions", label_font, value_font)
        row += 1
        self._add_metric_row(metrics_grid, row, "Totalt oppgaver", "total_questions", label_font, value_font)
        row += 1
        self._add_metric_row(metrics_grid, row, "Riktige svar", "correct_answers", label_font, value_font)
        row += 1
        self._add_metric_row(metrics_grid, row, "Nøyaktighet", "accuracy", label_font, value_font)
        row += 1

        # Sneglighet group (was "Hastighet (STPO)")
        hastighet_header = QLabel("Sneglighet:")
        hastighet_header.setFont(label_font)
        hastighet_header.setStyleSheet(f"color: {self.base_text_color}; background: transparent;")
        metrics_grid.addWidget(hastighet_header, row, 0, 1, 2)
        row += 1
        self._add_metric_row(metrics_grid, row, "└ Beste", "stpo_beste", label_font, value_font)
        row += 1
        self._add_metric_row(metrics_grid, row, "└ Siste", "stpo_siste", label_font, value_font)
        row += 1
        self._add_metric_row(metrics_grid, row, "└ Snitt", "stpo_snitt", label_font, value_font)
        row += 1

        metrics_grid.addItem(QSpacerItem(0, 16, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed), row, 0, 1, 2)
        row += 1

        self._add_metric_row(metrics_grid, row, "Sist spilt", "last_played", label_font, value_font)
        row += 1

        metrics_grid.addItem(QSpacerItem(0, 16, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed), row, 0, 1, 2)
        row += 1

        # Weak areas header
        weak_header = QLabel("Svake områder:")
        weak_header.setFont(label_font)
        weak_header.setStyleSheet(f"color: {self.base_text_color}; background: transparent;")
        metrics_grid.addWidget(weak_header, row, 0, 1, 2)
        row += 1

        self.weak_areas_label = QLabel("—")
        self.weak_areas_label.setFont(value_font)
        self.weak_areas_label.setStyleSheet(f"color: {self.muted_color}; background: transparent;")
        self.weak_areas_label.setWordWrap(True)
        metrics_grid.addWidget(self.weak_areas_label, row, 0, 1, 2)

        left_layout.addLayout(metrics_grid)

        columns_layout.addWidget(left_container, alignment=Qt.AlignmentFlag.AlignTop)
        columns_layout.setStretchFactor(left_container, 40)

        # === RIGHT COLUMN (60%) - Accuracy Chart ===
        right_container = QWidget()
        right_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_container.setStyleSheet("background: transparent; border: none;")
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        ui_chart_config = (self.ui_config.get('containers', {}) or {}).get('stats_modal', {}).get('chart', {})
        app_chart_config = self.stats_config.get('chart', {})
        chart_config = {**ui_chart_config, **app_chart_config}
        self.chart_widget = AccuracyChartWidget(chart_config, self)
        self.chart_widget.setMinimumSize(300, 400)
        right_layout.addWidget(self.chart_widget)

        # Chart mode toggle (Nøyaktighet / Sneglighet)
        self._chart_mode = "accuracy"
        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 10, 0, 0)
        toggle_row.setSpacing(0)
        toggle_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        toggle_font = create_font_px('Palatino Linotype', 18, QFont.Weight.Bold)
        toggle_style_active = """
            background-color: #007FFF;
            color: white;
            border: none;
            padding: 8px 20px;
        """
        toggle_style_inactive = """
            background-color: #E5E7EB;
            color: #1F2A37;
            border: none;
            padding: 8px 20px;
        """

        self.toggle_accuracy_btn = QPushButton("Nøyaktighet")
        self.toggle_accuracy_btn.setFont(toggle_font)
        self.toggle_accuracy_btn.setStyleSheet(toggle_style_active + "border-radius: 8px 0 0 8px;")
        self.toggle_accuracy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_accuracy_btn.clicked.connect(lambda: self._set_chart_mode("accuracy"))

        self.toggle_tpo_btn = QPushButton("Sneglighet")
        self.toggle_tpo_btn.setFont(toggle_font)
        self.toggle_tpo_btn.setStyleSheet(toggle_style_inactive + "border-radius: 0 8px 8px 0;")
        self.toggle_tpo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_tpo_btn.clicked.connect(lambda: self._set_chart_mode("tpo"))

        toggle_row.addWidget(self.toggle_accuracy_btn)
        toggle_row.addWidget(self.toggle_tpo_btn)
        right_layout.addLayout(toggle_row)

        columns_layout.addWidget(right_container, alignment=Qt.AlignmentFlag.AlignTop)
        columns_layout.setStretchFactor(right_container, 60)

        layout.addLayout(columns_layout)
        layout.addStretch(1)

    def _add_metric_row(self, grid, row: int, label_text: str, key: str, label_font, value_font) -> None:
        label = QLabel(label_text)
        label.setFont(label_font)
        label.setStyleSheet(f"color: {self.base_text_color}; background: transparent;")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(label, row, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        value_label = QLabel("—")
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {self.base_text_color}; background: transparent;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(value_label, row, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.left_value_labels[key] = value_label

    def _build_font(self, cfg: dict, default_size: int = 26, default_weight: str = 'bold'):
        cfg = cfg or {}
        family = cfg.get('family', 'Palatino Linotype')
        size = int(cfg.get('size', default_size))
        weight_str = cfg.get('weight', default_weight)
        weight = QFont.Weight.Bold if weight_str == 'bold' else QFont.Weight.Normal
        return create_font_px(family, size, weight)

    def refresh(self, module_stats: dict, daily_stats: dict) -> None:
        """Refresh stats display with current data."""
        module_stats = module_stats or {}
        daily_stats = daily_stats or {}

        total_sessions = module_stats.get('total_sessions', 0)
        if 'total_sessions' in self.left_value_labels:
            self.left_value_labels['total_sessions'].setText(str(total_sessions) if total_sessions else "—")

        total_q = module_stats.get('total_questions', 0)
        if 'total_questions' in self.left_value_labels:
            self.left_value_labels['total_questions'].setText(str(total_q) if total_q else "—")

        correct = module_stats.get('correct_answers', 0)
        if 'correct_answers' in self.left_value_labels:
            self.left_value_labels['correct_answers'].setText(str(correct) if correct else "—")

        if 'accuracy' in self.left_value_labels:
            if total_q > 0:
                acc = round(100 * correct / total_q)
                self.left_value_labels['accuracy'].setText(f"{acc}%")
            else:
                self.left_value_labels['accuracy'].setText("—")

        last_played = module_stats.get('last_played')
        if 'last_played' in self.left_value_labels:
            self.left_value_labels['last_played'].setText(self._format_timestamp(last_played))

        # STPO metrics (beste/siste/snitt)
        stpo_data = self._compute_stpo_metrics(daily_stats)
        if 'stpo_beste' in self.left_value_labels:
            self.left_value_labels['stpo_beste'].setText(f"{stpo_data['beste']}s" if stpo_data['beste'] else "—")
        if 'stpo_siste' in self.left_value_labels:
            self.left_value_labels['stpo_siste'].setText(f"{stpo_data['siste']}s" if stpo_data['siste'] else "—")
        if 'stpo_snitt' in self.left_value_labels:
            self.left_value_labels['stpo_snitt'].setText(f"{stpo_data['snitt']}s" if stpo_data['snitt'] else "—")

        self._update_weak_areas(daily_stats)
        self._update_chart(daily_stats)

    def _compute_stpo_metrics(self, daily_stats: dict) -> dict:
        """Compute STPO metrics: beste (min), siste (last), snitt (avg)."""
        all_stpo = []  # list of (date, stpo) for each day
        for date_str, day_data in sorted((daily_stats or {}).items()):
            if not isinstance(day_data, dict):
                continue
            sessions = day_data.get('logikkquiz', [])
            if not isinstance(sessions, list):
                continue
            day_seconds = 0
            day_tasks = 0
            for session in sessions:
                if not isinstance(session, dict):
                    continue
                try:
                    day_seconds += max(0, int(session.get('session_seconds', 0) or 0))
                    day_tasks += max(0, int(session.get('total_questions', 0) or 0))
                except Exception:
                    continue
            if day_tasks > 0 and day_seconds > 0:
                all_stpo.append((date_str, int(round(day_seconds / day_tasks))))
        
        if not all_stpo:
            return {'beste': None, 'siste': None, 'snitt': None}
        
        stpo_values = [s[1] for s in all_stpo]
        return {
            'beste': min(stpo_values),
            'siste': all_stpo[-1][1],  # last day
            'snitt': int(round(sum(stpo_values) / len(stpo_values)))
        }

    def _format_duration(self, seconds):
        """Format seconds as M:SS (or S sek if under a minute)."""
        if seconds is None:
            return "—"
        try:
            s = int(seconds)
        except Exception:
            return "—"
        if s <= 0:
            return "—"
        if s < 60:
            return f"{s} sek"
        minutes = s // 60
        rem = s % 60
        return f"{minutes}:{rem:02d}"

    def _format_timestamp(self, ts):
        """Format compact timestamp (20251231.091028) for display."""
        if not ts:
            return "—"
        try:
            if '.' in ts:
                date_part = ts.split('.')[0]
            else:
                date_part = ts[:8]
            if len(date_part) == 8:
                year = date_part[:4]
                month = date_part[4:6]
                day = date_part[6:8]
                return f"{day}.{month}.{year}"
        except Exception:
            pass
        return ts

    def _update_weak_areas(self, daily_stats: dict) -> None:
        """Analyze daily stats to find weak question types (3+ errors in last 30 days)."""
        from datetime import datetime, timedelta
        
        # Only consider last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        weak_counts: dict = {}
        for date_str, day_data in daily_stats.items():
            if date_str < cutoff_date:
                continue
            if not isinstance(day_data, dict):
                continue
            sessions = day_data.get('logikkquiz', [])
            for session in sessions:
                if isinstance(session, dict):
                    weaks = session.get('weaks', [])
                    for w in weaks:
                        weak_counts[w] = weak_counts.get(w, 0) + 1

        # Filter: only topics with 3+ errors
        weak_counts = {k: v for k, v in weak_counts.items() if v >= 3}

        if not weak_counts:
            self.weak_areas_label.setText("Ingen")
            self.weak_areas_label.setStyleSheet(f"color: {self.muted_color}; background: transparent;")
            return

        sorted_weaks = sorted(weak_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        weak_texts = [f"• {OPERATION_NAMES.get(w[0], w[0])} ({w[1]})" for w in sorted_weaks]
        self.weak_areas_label.setText("\n".join(weak_texts))
        self.weak_areas_label.setStyleSheet(f"color: {self.base_text_color}; background: transparent;")

    def _update_chart(self, daily_stats: dict) -> None:
        """Build chart data from daily logikkquiz sessions based on current mode."""
        self._daily_stats_cache = daily_stats
        if self._chart_mode == "tpo":
            self._update_chart_tpo(daily_stats)
        else:
            self._update_chart_accuracy(daily_stats)

    def _update_chart_accuracy(self, daily_stats: dict) -> None:
        """Build accuracy chart data from daily logikkquiz sessions."""
        chart_data: list = []
        for date_str in sorted(daily_stats.keys()):
            day_data = daily_stats.get(date_str)
            if not isinstance(day_data, dict):
                continue
            sessions = day_data.get('logikkquiz', [])
            day_correct = 0
            day_total = 0
            for session in sessions:
                if isinstance(session, dict):
                    day_correct += session.get('correct_answers', 0)
                    day_total += session.get('total_questions', 0)
            if day_total > 0:
                accuracy = round(100 * day_correct / day_total)
                chart_data.append({'date': date_str, 'accuracy': accuracy})

        self.chart_widget.set_data(chart_data)

    def _update_chart_tpo(self, daily_stats: dict) -> None:
        """Build TPO (time per oppgave) chart data from daily logikkquiz sessions."""
        chart_data: list = []
        for date_str in sorted(daily_stats.keys()):
            day_data = daily_stats.get(date_str)
            if not isinstance(day_data, dict):
                continue
            sessions = day_data.get('logikkquiz', [])
            day_seconds = 0
            day_total = 0
            for session in sessions:
                if isinstance(session, dict):
                    day_seconds += max(0, int(session.get('session_seconds', 0) or 0))
                    day_total += max(0, int(session.get('total_questions', 0) or 0))
            if day_total > 0 and day_seconds > 0:
                tpo = round(day_seconds / day_total)
                chart_data.append({'date': date_str, 'accuracy': tpo})

        self.chart_widget.set_data(chart_data, mode="tpo")

    def _set_chart_mode(self, mode: str) -> None:
        """Switch chart between accuracy and TPO modes."""
        if mode == self._chart_mode:
            return
        self._chart_mode = mode

        active_style = """
            background-color: #007FFF;
            color: white;
            border: none;
            padding: 8px 20px;
        """
        inactive_style = """
            background-color: #E5E7EB;
            color: #1F2A37;
            border: none;
            padding: 8px 20px;
        """
        if mode == "accuracy":
            self.toggle_accuracy_btn.setStyleSheet(active_style + "border-radius: 8px 0 0 8px;")
            self.toggle_tpo_btn.setStyleSheet(inactive_style + "border-radius: 0 8px 8px 0;")
        else:
            self.toggle_accuracy_btn.setStyleSheet(inactive_style + "border-radius: 8px 0 0 8px;")
            self.toggle_tpo_btn.setStyleSheet(active_style + "border-radius: 0 8px 8px 0;")

        if hasattr(self, '_daily_stats_cache') and self._daily_stats_cache:
            self._update_chart(self._daily_stats_cache)


# Question generation helper functions
def rand_int(min_val: int, max_val: int) -> int:
    """Generate random integer in range"""
    return random.randint(min_val, max_val)


def shuffle_list(items: list) -> list:
    """Shuffle list and return new list"""
    shuffled = items.copy()
    random.shuffle(shuffled)
    return shuffled


def pluralize_category(category: str) -> str:
    """Convert category name to plural (flertall) for Norwegian.
    
    Used with 'Noen', 'Alle', 'Ingen' which require plural nouns.
    
    Example: 'romvesen' -> 'romvesener'
             'fabeldyr' -> 'fabeldyr' (unchanged, -dyr is already plural)
    """
    # Categories ending in -dyr stay unchanged (fabeldyr, mutantdyr)
    if category.endswith('dyr'):
        return category
    # Categories ending in -vesen add -er
    if category.endswith('vesen'):
        return f"{category}er"
    # Categories ending in -hyre add -r
    if category.endswith('hyre'):
        return f"{category}r"
    # Default: add -er
    return f"{category}er"


def get_indefinite_one(category: str) -> str:
    """Get correct indefinite numeral 'one' for Norwegian gender agreement.
    
    Intetkjønn (neuter) uses 'ett', hankjønn/hunkjønn use 'én'.
    
    Example: 'fabeldyr' -> 'ett' (et fabeldyr)
             'romvesen' -> 'ett' (et romvesen)
             'robot' -> 'én' (en robot)
    """
    # Intetkjønn categories use 'ett'
    INTETKJONN = {'dyr', 'vesen', 'hyre'}
    for suffix in INTETKJONN:
        if category.endswith(suffix):
            return "ett"
    return "én"

def negate_verb_phrase(phrase: str) -> str:
    """Insert 'ikke' after the first word (verb) in a phrase.
    Norwegian main clause: Subject + Verb + ikke + rest
    Example: 'svever i stua' -> 'svever ikke i stua'
    """
    parts = phrase.split(' ', 1)
    if len(parts) == 2:
        return f"{parts[0]} ikke {parts[1]}"
    return f"{parts[0]} ikke"


def modalize(modal: str, phrase: str) -> str:
    """Return a modal + infinitive version of a verb phrase.

    Example: modalize('må', 'teleporterer en laser') -> 'må teleportere en laser'
    """
    modal_clean = (modal or "").strip()
    if not modal_clean:
        return to_infinitiv(phrase)
    return f"{modal_clean} {to_infinitiv(phrase)}".strip()


def negate_leddsetning(phrase: str) -> str:
    """Insert 'ikke' before the verb (first word) for subordinate clauses.
    Norwegian subordinate clause (after hvis, at, som): Subject + ikke + Verb + rest
    Example: 'svever i stua' -> 'ikke svever i stua'
    """
    return f"ikke {phrase}"


def to_infinitiv(phrase: str) -> str:
    """Convert Norwegian verb phrase from presens to infinitiv.
    
    Norwegian presens typically ends in -r, infinitiv removes it.
    Only truly irregular verbs need exceptions.
    
    Example: 'danser i kanelen' -> 'danse i kanelen'
             'gjør noe galt' -> 'gjøre noe galt'
    """
    # Only REAL irregular verbs where removing -r doesn't work
    IRREGULAR = {
        'er': 'være',       # er -> være (not "e")
        'har': 'ha',        # har -> ha (not "ha" via -r rule)
        'vet': 'vite',      # no -r ending
        'gjør': 'gjøre',    # gjør -> gjøre (not "gjø")
        'spør': 'spørre',   # spør -> spørre (not "spø")
        'tør': 'tørre',     # tør -> tørre (not "tø")
        'bør': 'burde',     # modal
        'kan': 'kunne',     # modal, no -r
        'vil': 'ville',     # modal, no -r
        'skal': 'skulle',   # modal, no -r
        'må': 'måtte',      # modal, no -r
        'sier': 'si',       # sier -> si (not "sie")
    }
    
    parts = phrase.split(' ', 1)
    verb = parts[0]
    
    # Check irregular first
    verb_lower = verb.lower()
    if verb_lower in IRREGULAR:
        inf_verb = IRREGULAR[verb_lower]
        if verb[0].isupper():
            inf_verb = inf_verb.capitalize()
    elif verb.endswith('r'):
        inf_verb = verb[:-1]
    else:
        inf_verb = verb
    
    return f"{inf_verb} {parts[1]}" if len(parts) > 1 else inf_verb


class LogicQuestionGenerator:
    """Generate logic questions based on configuration templates"""
    
    def __init__(self, config: dict, difficulty: int = 1):
        self.config = config
        self.difficulty = difficulty
        self.entities = config.get("entities", {})
        self.properties = config.get("properties", {})
        self.properties_transitive = config.get("properties_transitive", {})
        self.properties_prepositional = config.get("properties_prepositional", {})
        self.objects = config.get("objects", {})
        self.operation_types = config.get("operation_types", [])
        self.mutant_gen = config.get("mutant_generator", {})
        
        # Validate all operation_types have generators
        self._validate_operation_types()
    
    def _validate_operation_types(self) -> None:
        """Validate all operation_types in config have corresponding generator methods."""
        for op_type in self.operation_types:
            op_id = op_type.get("id", "")
            method_name = f"generate_{op_id}"
            if not hasattr(self, method_name):
                log_error_event(
                    "LogikkQuiz",
                    f"Missing generator for operation_type '{op_id}'",
                    f"Expected method: {method_name}"
                )

    def _absurd_preface(self) -> str:
        return random.choice(
            [
                "Magisk regel:",
                "Troll-logikk sier:",
                "I Absurd-Land gjelder dette:",
                "Hemmelig regel fra en vaffel-robot:",
                "Notis fra en kanel-komité:",
                "En professor i sokker mumler:",
                "Rykte fra en snakkende potet:",
                "Obs! En usynlig pingvin påstår:",
                "Kosekoden lyder:",
            ]
        )

    def _absurd_tag(self) -> str:
        return random.choice(
            [
                "",
                " (ikke spør hvorfor)",
                " (universet fniser litt)",
                " (det står i bolla)",
                " (kilden er en papegøye)",
                " (100% seriøs, 0% normal)",
            ]
        )

    def _with_preface(self, core: str) -> str:
        if random.random() < 0.65:
            return f"{self._absurd_preface()}\n{core}{self._absurd_tag()}"
        return core

    def _pick_question(self, base: list[str], extra: list[str] | None = None) -> str:
        options = [q for q in base if isinstance(q, str) and q.strip()]
        if extra:
            options.extend([q for q in extra if isinstance(q, str) and q.strip()])
        return random.choice(options) if options else "Hva følger?"
    
    def _generate_mutant_entity(self) -> str:
        """Generate a random mutant entity name from prefixes/suffixes + base words.
        Examples: 'trollkatt', 'snøbanan', 'elefanttass', 'froskkrabat'
        """
        prefixes = self.mutant_gen.get("prefixes", [])
        suffixes = self.mutant_gen.get("suffixes", [])
        animals = self.mutant_gen.get("base_animals", [])
        plants = self.mutant_gen.get("base_plants", [])
        bases = animals + plants
        
        if not bases:
            return "mutant"
        
        base = random.choice(bases)
        mode = random.choice(["prefix", "suffix"])
        
        if mode == "prefix" and prefixes:
            return f"{random.choice(prefixes)}{base}"
        elif mode == "suffix" and suffixes:
            return f"{base}{random.choice(suffixes)}"
        elif prefixes:
            return f"{random.choice(prefixes)}{base}"
        else:
            return base

    def _get_objects_for_theme(self, theme: str, kind: str = "obj") -> list[str]:
        if kind not in {"obj", "who"}:
            kind = "obj"

        def normalize_list(value: object) -> list[str]:
            if not isinstance(value, list):
                return []
            return [o.strip() for o in value if isinstance(o, str) and o.strip()]

        def pick_from(entry: object) -> list[str]:
            if isinstance(entry, dict):
                return normalize_list(entry.get(kind))
            # Backwards-compat: theme/default can be a plain list.
            return normalize_list(entry)

        if isinstance(self.objects, dict):
            theme_objects = pick_from(self.objects.get(theme))
            if theme_objects:
                return theme_objects

            default_objects = pick_from(self.objects.get("default"))
            if default_objects:
                return default_objects

        return ["en venn"] if kind == "who" else ["noe"]

    def _render_property(self, theme: str, phrase: str) -> str:
        if not isinstance(phrase, str):
            return "har egenskap"
        needs_obj = ("{obj}" in phrase) or ("{object}" in phrase)
        needs_who = ("{who}" in phrase)

        if needs_obj or needs_who:
            obj = random.choice(self._get_objects_for_theme(theme, kind="obj"))
            who = random.choice(self._get_objects_for_theme(theme, kind="who"))
            try:
                return phrase.format(obj=obj, object=obj, who=who)
            except Exception:
                return (
                    phrase.replace("{obj}", obj)
                    .replace("{object}", obj)
                    .replace("{who}", who)
                )
        return phrase

    def _get_random_property_phrase(self, theme: str, forbidden: set[str] | None = None) -> str:
        forbidden_lc = {s.strip().lower() for s in (forbidden or set()) if isinstance(s, str)}

        intrans = self.properties.get(theme, []) if isinstance(self.properties, dict) else []
        trans = self.properties_transitive.get(theme, []) if isinstance(self.properties_transitive, dict) else []
        prep = (
            self.properties_prepositional.get(theme, [])
            if isinstance(self.properties_prepositional, dict)
            else []
        )

        def clean(source: object) -> list[str]:
            if not isinstance(source, list):
                return []
            out: list[str] = []
            for item in source:
                if not isinstance(item, str):
                    continue
                text = item.strip()
                if not text:
                    continue
                if text.lower() in forbidden_lc:
                    continue
                out.append(text)
            return out

        pools = [clean(intrans), clean(trans), clean(prep)]
        pools = [p for p in pools if p]
        if not pools:
            return "har egenskap"

        # Pick a pool first so transitive/prepositional do not get drowned out.
        for _ in range(20):
            pool = random.choice(pools)
            raw = random.choice(pool)
            rendered = self._render_property(theme, raw).strip()
            if rendered and rendered.lower() not in forbidden_lc:
                return rendered

        return "har egenskap"
    
    def _get_random_entity_and_properties(self, theme: str) -> tuple[str, str, str]:
        """Get random entity and two different properties for a theme"""
        theme_entities = self.entities.get(theme, ["X"])
        
        # 15% chance to use mutant generator instead of static entity
        if self.mutant_gen and random.random() < 0.15:
            entity = self._generate_mutant_entity()
        else:
            entity = random.choice(theme_entities)

        prop_a = self._get_random_property_phrase(theme)
        prop_b = self._get_random_property_phrase(theme, forbidden={prop_a})
        
        return entity, prop_a, prop_b

    def _get_random_individual_name(self, forbidden: set[str] | None = None) -> str:
        """Pick an individual name from config-driven pools (no hardcoded names).

        Uses the existing entity vocab (romvesen/folkevesen/etc) and optionally the
        mutant generator. `forbidden` prevents awkward cases like "Glorp er en glorp".
        """
        forbidden_lc = {s.strip().lower() for s in (forbidden or set()) if isinstance(s, str)}

        candidates: list[str] = []
        try:
            for _theme, words in (self.entities or {}).items():
                if not isinstance(words, list):
                    continue
                for w in words:
                    if not isinstance(w, str):
                        continue
                    w_norm = w.strip()
                    if not w_norm:
                        continue
                    if w_norm.lower() in forbidden_lc:
                        continue
                    candidates.append(w_norm)
        except Exception:
            candidates = []

        # Add a few mutant-generated candidates when available.
        if self.mutant_gen:
            for _ in range(3):
                try:
                    m = self._generate_mutant_entity()
                    if isinstance(m, str) and m.strip() and m.strip().lower() not in forbidden_lc:
                        candidates.append(m.strip())
                except Exception:
                    pass

        if not candidates:
            return "X"

        name = random.choice(candidates)
        # Ensure it reads like a proper noun in Norwegian UI.
        return name[:1].upper() + name[1:]

    def _get_random_theme_and_class(self) -> tuple[str, str]:
        """Pick a theme and a class word (an entity from that theme)."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "romvesen"
        class_word = random.choice(self.entities.get(theme, ["glorp"]))
        return theme, class_word
    
    def generate_modus_ponens(self, op_type: dict) -> dict:
        """Generate modus ponens question: If A then B. A is true. Therefore?"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        statement = self._with_preface(
            f"Hvis {entity} {prop_a}, så {entity} {prop_b}.\n{entity.capitalize()} {prop_a}."
        )
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva følger logisk av dette?",
                "Hva er den riktige slutningen?",
                "Hva må stemme da?",
            ],
            extra=[
                "Hva sier denne rare regelen oss?",
                "Hva MÅ være sant nå?",
                "Hva er den minst sprø konklusjonen?",
            ],
        )
        
        # Correct answer
        correct = f"{entity.capitalize()} {prop_b}"
        
        # Distractors based on difficulty
        distractors = self._get_distractors_modus_ponens(entity, prop_a, prop_b)
        
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "modus_ponens"
        }
    
    def generate_modus_tollens(self, op_type: dict) -> dict:
        """Generate modus tollens question: If A then B. B is false. Therefore?"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        statement = self._with_preface(
            f"Hvis {entity} {prop_a}, så {entity} {prop_b}.\n{entity.capitalize()} {negate_verb_phrase(prop_b)}."
        )
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva følger av dette?",
                "Hvilken slutning er riktig?",
                "Hva kan vi utlede?",
            ],
            extra=[
                "Hva avslører dette om den første tingen?",
                "Hva må være falskt nå?",
                "Hva sier logikk-gremlinen?",
            ],
        )
        
        # Correct: entity does NOT have prop_a (main clause: verb + ikke + rest)
        correct = f"{entity.capitalize()} {negate_verb_phrase(prop_a)}"
        
        distractors = self._get_distractors_modus_tollens(entity, prop_a, prop_b)
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "modus_tollens"
        }
    
    def generate_universal_instantiation(self, op_type: dict) -> dict:
        """Generate universal instantiation: All X have Y. Z is X. Therefore?"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["X"])
        
        category = theme
        category_pl = pluralize_category(category)
        entity = random.choice(theme_entities)
        prop = self._get_random_property_phrase(theme)
        
        statement = self._with_preface(
            f"Alle {category_pl} {prop}.\n{entity.capitalize()} er et {category}."
        )
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva gjelder da for dette vesenet?",
                "Hva følger av disse premissene?",
                "Hva vet vi nå?",
            ],
            extra=[
                "Hva må gjelde for akkurat dette eksemplaret?",
                "Hva sier regelen om denne figuren?",
            ],
        )
        
        correct = f"{entity.capitalize()} {prop}"
        
        distractors = [
            f"Noen {category_pl} {negate_verb_phrase(prop)}",
            f"Bare noen {category_pl} {prop}"
        ]
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "universal_instantiation"
        }
    
    def generate_disjunctive_syllogism(self, op_type: dict) -> dict:
        """Generate disjunctive syllogism: A or B. Not A. Therefore?"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["X", "Y"])
        
        if len(theme_entities) >= 2:
            entity_a, entity_b = random.sample(theme_entities, 2)
        else:
            entity_a, entity_b = "A", "B"
        
        statement = self._with_preface(
            f"Enten er det {entity_a} eller {entity_b}.\nDet er ikke {entity_a}."
        )
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva gjenstår som mulighet?",
                "Hva må da stemme?",
                "Hvilken slutning kan vi trekke?",
            ],
            extra=[
                "Hvem står igjen på scenen?",
                "Hvilken mulighet overlever?",
            ],
        )
        
        correct = f"Det er {entity_b}"
        
        distractors = [
            f"Det er {entity_a}",
            f"Det kan være begge deler"
        ]
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "disjunctive_syllogism"
        }
    
    def generate_hypothetical_syllogism(self, op_type: dict) -> dict:
        """Generate hypothetical syllogism: If A then B. If B then C. Therefore?"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        prop_a = self._get_random_property_phrase(theme)
        prop_b = self._get_random_property_phrase(theme, forbidden={prop_a})
        prop_c = self._get_random_property_phrase(theme, forbidden={prop_a, prop_b})
        subject = random.choice(self.entities.get(theme, ["glorp"]))
        subject_name = subject.capitalize()
        
        statement = self._with_preface(
            (
                f"Hvis {subject_name} {prop_a}, så {subject_name} {prop_b}.\n"
                f"Hvis {subject_name} {prop_b}, så {subject_name} {prop_c}."
            )
        )
        question = self._pick_question(
            [
                "Hva følger?",
                "Kan vi koble disse reglene sammen?",
                "Hva kan vi slutte fra hele kjeden?",
                "Hva er den logiske forbindelsen?",
            ],
            extra=[
                "Hva får du hvis du stapler reglene oppå hverandre?",
                "Hvis dette var dominobrikker: hva velter til slutt?",
            ],
        )
        
        correct = f"Hvis {subject_name} {prop_a}, så {subject_name} {prop_c}"
        
        distractors = [
            f"Hvis {subject_name} {prop_c}, så {subject_name} {prop_a}",
            f"Hvis {subject_name} {prop_b}, så {subject_name} {prop_a}"
        ]
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "hypothetical_syllogism"
        }
    
    def generate_contraposition(self, op_type: dict) -> dict:
        """Generate contraposition: If A then B. Equivalent to: If not B then not A."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)

        statement = self._with_preface(f"Hvis {entity} {prop_a}, så {entity} {prop_b}.")
        question = self._pick_question(
            [
                "Hvilken påstand er logisk ekvivalent?",
                "Hvilken setning betyr det samme?",
                "Hvilken påstand sier akkurat det samme?",
                "Hva er en annen måte å si dette på?",
            ],
            extra=[
                "Hvilken setning sier det samme, bare baklengs-logisk?",
                "Hva er den samme regelen, men med omvendt vri?",
                "Hva sier regelen hvis vi snur den som en pannekake?",
            ],
        )
        
        correct = f"Hvis {entity} {negate_leddsetning(prop_b)}, så {entity} {negate_verb_phrase(prop_a)}"
        
        distractors = [
            f"Hvis {entity} {prop_b}, så {entity} {prop_a}",
            f"Hvis {entity} {negate_leddsetning(prop_a)}, så {entity} {negate_verb_phrase(prop_b)}"
        ]
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "contraposition"
        }
    
    def generate_existential_instantiation(self, op_type: dict) -> dict:
        """Generate existential instantiation: Some X have Y. Therefore?"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        category = theme
        category_pl = pluralize_category(category)
        one = get_indefinite_one(category)
        prop = self._get_random_property_phrase(theme)
        
        statement = self._with_preface(f"Noen {category_pl} {prop}.")
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva vet vi med sikkerhet?",
                "Hva følger av denne påstanden?",
                "Hva er det minste vi kan si?",
            ],
            extra=[
                "Hva er den minste biten av sannhet her?",
                "Hva kan vi si uten å overdrive som en enhjørning?",
            ],
        )
        
        correct = f"Minst {one} {category} {prop}."
        
        distractors = [
            f"Alle {category_pl} {prop}.",
            f"Ingen {category_pl} {prop}."
        ]
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "existential_instantiation"
        }
    
    def generate_negation_introduction(self, op_type: dict) -> dict:
        """Bayesian model update: hypothesis + new evidence → revise belief.
        
        Structure:
        1. Past hypothesis: "Vi antok at alle X kan Y" (general claim about class)
        2. New evidence: "Senere lærte vi at Z ikke kan Y" (counterexample)
        3. Question: "Hva er den mest rimelige konklusjonen?"
        
        Correct answer: minimal model update (the hypothesis was wrong)
        Distractors: 
        - Z is not an X (ad-hoc assumption)
        - We can't conclude anything (false agnosticism)
        
        This teaches Bayesian updating, not theatrical reductio.
        """
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["eksempel"])
        
        category = theme
        category_pl = pluralize_category(category)
        counterexample = random.choice(theme_entities)
        prop = self._get_random_property_phrase(theme)
        
        # Convert property to "kan + infinitive" form for hypothesis
        prop_infinitive = to_infinitiv(prop)
        
        # Past hypothesis + new evidence structure
        hypothesis = f"alle {category_pl} kan {prop_infinitive}"
        new_evidence = f"{counterexample.capitalize()} ikke kan {prop_infinitive}"
        
        statement = self._with_preface(
            f"Vi antok at {hypothesis}.\nNå fikk vi vite at {new_evidence}."
        )
        question = self._pick_question(
            [
                "Hva er den mest rimelige konklusjonen?",
                "Hva bør vi tenke nå?",
                "Hvordan endrer dette det vi trodde?",
                "Hva er den beste forklaringen?",
            ],
            extra=[
                "Hva gjør vi når virkeligheten dytter oss i panna?",
                "Hva er den minst dramatiske oppdateringen?",
            ],
        )
        
        # Correct: disjunction - one of two must be wrong, but we don't know which
        correct = f"Enten er {counterexample.capitalize()} ikke et {category}, eller antagelsen var feil."
        
        if self.difficulty == 1:
            distractors = [
                f"{counterexample.capitalize()} er ikke et {category}.",  # Too strong - claims to know which
                f"Antagelsen var helt feil."  # Too strong - claims to know which
            ]
        elif self.difficulty == 2:
            distractors = [
                f"Vi må forkaste alt vi vet om {category_pl}.",  # Overreaction
                f"Vi kan ikke konkludere noe som helst."  # False agnosticism
            ]
        else:
            # Level 3: trickier distractors
            distractors = [
                f"Antagelsen er trolig feil.",  # Premature Bayes - jumps to probability without justification
                f"Begge påstandene kan være sanne samtidig."  # Contradiction acceptance
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "negation_introduction"
        }
    
    def generate_insufficient_info(self, op_type: dict) -> dict:
        """Generate insufficient info question where correct answer is 'Vi vet ikke'"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_pl = pluralize_category(theme)
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        # Premise that doesn't allow conclusion
        statement = f"Noen {theme_pl} {prop_a}.\n{entity.capitalize()} er et {theme}."
        question = f"Hva vet vi om {entity}?"
        
        # Vary the "we don't know" phrasing
        uncertainty_options = [
            "Det kan vi ikke vite",
            "Ikke nok informasjon",
            "Premissene sier ingenting om dette",
            "Vi mangler data",
            "Det følger ikke fra premissene",
        ]
        correct = random.choice(uncertainty_options)
        
        distractors = [
            f"{entity.capitalize()} {prop_a}",
            f"{entity.capitalize()} {negate_verb_phrase(prop_a)}"
        ]
        options = shuffle_list([correct] + distractors[:2])
        
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "insufficient_info"
        }
    
    def _get_distractors_modus_ponens(self, entity: str, prop_a: str, prop_b: str) -> list:
        """Get distractors for modus ponens based on difficulty"""
        if self.difficulty == 1:
            # Obvious wrong answers
            return [
                f"{entity.capitalize()} {negate_verb_phrase(prop_b)}",
                f"{entity.capitalize()} {negate_verb_phrase(prop_a)}"
            ]
        elif self.difficulty == 2:
            # Affirming consequent fallacy
            return [
                f"{entity.capitalize()} {prop_a}",  # Affirming consequent
                f"{entity.capitalize()} kanskje {prop_b}"
            ]
        else:
            # Subtle distractors
            return [
                f"Hvis {entity} {prop_b}, så {entity} {prop_a}",  # Inverse fallacy
                f"{entity.capitalize()} {prop_a} også"
            ]
    
    def _get_distractors_modus_tollens(self, entity: str, prop_a: str, prop_b: str) -> list:
        """Get distractors for modus tollens based on difficulty"""
        if self.difficulty == 1:
            return [
                f"{entity.capitalize()} {prop_a}",
                f"{entity.capitalize()} {prop_b}"
            ]
        elif self.difficulty == 2:
            # Denying antecedent fallacy
            return [
                f"{entity.capitalize()} {prop_b}",
                f"{entity.capitalize()} kanskje {prop_a}"
            ]
        else:
            return [
                f"Hvis {entity} {negate_leddsetning(prop_a)}, så {entity} {negate_verb_phrase(prop_b)}",
                f"{entity.capitalize()} kanskje {prop_a}"
            ]

    # ========== NEW OPERATION GENERATORS ==========
    
    def generate_conjunction(self, op_type: dict) -> dict:
        """Conjunction: A AND B. A is true, B is true. Therefore A AND B is true."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        subject_name = entity.capitalize()

        # Style variation: avoid robotic repetition "X ...\nX ..." sometimes.
        if random.random() < 0.55:
            statement = f"{subject_name} {prop_a}.\n{subject_name} {prop_b}."
        else:
            statement = f"{subject_name} {prop_a}\nog {prop_b}."
        question = random.choice([
            "Hva kan vi si?",
            "Hva kan vi slå fast om begge egenskapene?",
            "Hva følger av disse to faktaene?",
            "Hvordan kan vi oppsummere dette?",
        ])
        
        correct = f"{subject_name} {prop_a} og {prop_b}"
        
        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {negate_verb_phrase(prop_a)}",
                f"{entity.capitalize()} bare {prop_a}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{entity.capitalize()} enten {prop_a} eller {prop_b}",
                f"{entity.capitalize()} {prop_a}, men {entity.capitalize()} {negate_verb_phrase(prop_b)}"
            ]
        else:
            distractors = [
                f"{entity.capitalize()} {prop_a} eller {prop_b}",
                f"Alle som {prop_a} også {prop_b}"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "conjunction"
        }
    
    def generate_disjunction_incl(self, op_type: dict) -> dict:
        """Inclusive OR: A OR B (or both). One is true, so statement is true."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        subject_name = entity.capitalize()
        
        a_text = f"{subject_name} {prop_a}"
        not_a_text = f"{subject_name} {negate_verb_phrase(prop_a)}"
        b_text = f"{subject_name} {prop_b}"
        not_b_text = f"{subject_name} {negate_verb_phrase(prop_b)}"
        both_text = f"{subject_name} {prop_a} og {prop_b}"
        not_both_text = f"Det er ikke sant at {subject_name} både {prop_a} og {prop_b}"

        premise_mode = random.choice(["a_and_b", "not_a_and_b", "a_and_not_b", "not_a_not_b"])

        premise_text = f"{subject_name} {prop_a}, og {prop_b} nå."
        forbidden = {a_text, b_text, both_text}
        a_val, b_val = True, True
        if premise_mode == "not_a_and_b":
            premise_text = f"{subject_name} {negate_verb_phrase(prop_a)}, og {prop_b} nå."
            forbidden = {not_a_text, b_text}
            a_val, b_val = False, True
        elif premise_mode == "a_and_not_b":
            premise_text = f"{subject_name} {prop_a}, og {negate_verb_phrase(prop_b)} nå."
            forbidden = {a_text, not_b_text}
            a_val, b_val = True, False
        elif premise_mode == "not_a_not_b":
            premise_text = f"{subject_name} {negate_verb_phrase(prop_a)}, og {negate_verb_phrase(prop_b)} nå."
            forbidden = {not_a_text, not_b_text}
            a_val, b_val = False, False

        # Avoid a "correct" option that merely restates the premise in another wording.
        forbidden_correct = set(forbidden)
        if premise_mode == "a_and_not_b":
            forbidden_correct.add(f"{subject_name} {prop_a}, men {subject_name} {negate_verb_phrase(prop_b)}")
        elif premise_mode == "not_a_and_b":
            forbidden_correct.add(f"{subject_name} {prop_b}, men {subject_name} {negate_verb_phrase(prop_a)}")

        statement = f"{subject_name} kan {to_infinitiv(prop_a)} eller {to_infinitiv(prop_b)} – eller begge deler samtidig.\n{premise_text}"

        question_pool = [
            "Hvilken av følgende påstander må være sann ut fra premissene?",
            "Hvilken av disse setningene følger logisk av premissene?",
            "Hvilken av disse setningene ikke følger logisk av premissene?",
        ]

        if premise_mode == "not_a_not_b":
            question = question_pool[0]
            correct = "Premissene motsier hverandre"
            distractors = [
                "Premissene er konsistente",
                f"{subject_name} {prop_a} eller {prop_b}",
            ]
        else:
            question = random.choice(question_pool)

            # Meta-level conclusions that follow but don't repeat the premise verbatim.
            meta_exactly_one = f"{subject_name} gjør akkurat én av tingene nå"
            meta_not_both_now = f"Det er ikke sant at {subject_name} både {prop_a} og {prop_b} nå"
            meta_both_now = f"Det er sant at {subject_name} både {prop_a} og {prop_b} nå"

            candidates = [
                (a_text, a_val, 2),
                (not_a_text, not a_val, 2),
                (b_text, b_val, 2),
                (not_b_text, not b_val, 2),
                (both_text, a_val and b_val, 4),
                (not_both_text, not (a_val and b_val), 4),
                (f"{subject_name} {prop_a}, men {subject_name} {negate_verb_phrase(prop_b)}", a_val and not b_val, 5),
                (f"{subject_name} {prop_b}, men {subject_name} {negate_verb_phrase(prop_a)}", b_val and not a_val, 5),
                (f"{subject_name} {prop_a} eller {prop_b}, men ikke begge på samme tid", a_val != b_val, 3),
                (f"{subject_name} {prop_a} og {prop_b} samtidig", a_val and b_val, 4),
                (meta_exactly_one, a_val != b_val, 7),
                (meta_not_both_now, not (a_val and b_val), 6),
                (meta_both_now, a_val and b_val, 6),
            ]

            # Remove direct premise copies (and near-duplicates that restate the premise).
            candidates = [c for c in candidates if c[0] not in forbidden_correct]

            true_opts = [(t, strength) for t, is_true, strength in candidates if is_true]
            false_opts = [(t, strength) for t, is_true, strength in candidates if not is_true]

            def pick_best(options: list[tuple[str, int]]) -> str:
                max_strength = max(s for _, s in options)
                best = [t for t, s in options if s == max_strength]
                return random.choice(best)

            if "ikke følger" in question:
                pool = false_opts or true_opts
                other_pool = true_opts or false_opts
            else:
                pool = true_opts or false_opts
                other_pool = false_opts or true_opts

            correct = pick_best(pool)
            distractors_pool: list[tuple[str, int]] = [(t, strength) for t, strength in other_pool if t != correct]
            if len(distractors_pool) < 2:
                distractors_pool = [(t, strength) for t, _, strength in candidates if t != correct]

            chosen_distractors = random.sample(distractors_pool, 2)
            distractors = [t for t, _strength in chosen_distractors]
            distractor_strengths = [strength for _t, strength in chosen_distractors]

        # Inject a rare absurd option for Wojnarowski-style humor
        # Always include one mild humorous option for Wojnarowski-style flavor
        funny_options = [
            f"{subject_name} liker ikke å gjøre to ting samtidig",
            f"{subject_name} blir sliten av å gjøre to ting samtidig",
            f"{subject_name} foretrekker å gjøre én ting om gangen",
            f"{subject_name} unngår å gjøre to ting samtidig",
            f"{subject_name} mister konsentrasjonen når alt skjer på en gang",
            f"{subject_name} velger helst én ting av gangen",
        ]
        funny = random.choice(funny_options)

        # Replace the dumbest (most obvious) distractor with the funny option.
        if funny != correct and funny not in distractors and distractors:
            replace_idx = 0
            if premise_mode == "not_a_not_b":
                # In the contradiction branch, "Premissene er konsistente" is the most obvious wrong.
                if "Premissene er konsistente" in distractors:
                    replace_idx = distractors.index("Premissene er konsistente")
            else:
                # Prefer replacing the lowest-strength distractor when available.
                if 'distractor_strengths' in locals() and len(distractor_strengths) == len(distractors):
                    replace_idx = min(range(len(distractor_strengths)), key=lambda i: distractor_strengths[i])
            distractors[replace_idx] = funny
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "disjunction_incl"
        }
    
    def generate_disjunction_excl(self, op_type: dict) -> dict:
        """Exclusive OR: A XOR B (exactly one). If A then not B."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        statement = f"Alltid enten {entity} {prop_a} eller {entity} {prop_b} – men ikke begge på samme tid.\n{entity.capitalize()} {prop_a} nå."
        question = random.choice([
            "Hva kan vi konkludere?",
            "Hva betyr dette for den andre egenskapen?",
            "Hva følger av dette?",
            "Hva kan vi si med sikkerhet?",
        ])
        
        correct = f"{entity.capitalize()} {negate_verb_phrase(prop_b)}."
        
        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {prop_b}.",  # Direct contradiction
                f"{entity.capitalize()} {prop_a} og {prop_b}."  # Violates XOR
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{entity.capitalize()} kanskje {prop_b}.",  # Modality instead of deduction
                f"{entity.capitalize()} kan også {prop_b}."  # Confuses XOR with OR
            ]
        else:
            distractors = [
                f"{entity.capitalize()} {prop_b} noen ganger.",  # Temporal confusion - "sometimes" vs XOR
                f"{entity.capitalize()} verken {prop_a} eller {prop_b}."  # Neither - wrong inference from XOR
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "disjunction_excl"
        }
    
    def generate_double_negation(self, op_type: dict) -> dict:
        """Double negation: NOT(NOT A) = A"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        # Use negate_leddsetning for subordinate clause after "at"
        statement = self._with_preface(
            f"Det er ikke sant at {entity} {negate_leddsetning(prop_a)}."
        )
        question = self._pick_question(
            [
                "Hva betyr dette?",
                "Hva sier denne setningen egentlig?",
                "Hva er den enkleste tolkningen?",
                "Hva følger av denne påstanden?",
            ],
            extra=[
                "Hva prøver denne setningen å si, med to lag 'ikke'?",
                "Hva står igjen når vi skreller bort 'ikke'?",
            ],
        )
        
        correct = f"{entity.capitalize()} {prop_a}"
        
        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {negate_verb_phrase(prop_a)}",
                "Setningen gir ingen mening"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{entity.capitalize()} kanskje {prop_a}",
                "Setningen er selvmotsigende"
            ]
        else:
            distractors = [
                f"Det er usikkert om {entity} {prop_a}",
                f"{entity.capitalize()} {prop_a} noen ganger"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "double_negation"
        }
    
    def generate_quantifier_all(self, op_type: dict) -> dict:
        """Universal quantifier: ALL X have Y. Some X exists. Therefore that X has Y."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["eksempel"])
        
        category = theme
        category_pl = pluralize_category(category)
        entity = random.choice(theme_entities)
        prop = self._get_random_property_phrase(theme)
        
        statement = self._with_preface(
            f"Alle {category_pl} {prop}.\n{entity.capitalize()} er et {category}."
        )
        question = self._pick_question(
            [
                "Hva følger?",
                "Hva gjelder da for dette vesenet?",
                "Hva kan vi si om dette tilfellet?",
                "Hvilken egenskap må dette vesenet ha?",
            ],
            extra=[
                "Hva tvinger denne regelen fram?",
                "Hva må være sant om dette vesnet nå?",
            ],
        )
        
        correct = f"{entity.capitalize()} {prop}"
        
        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {negate_verb_phrase(prop)}",
                f"Bare noen {category_pl} {prop}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"Noen {category_pl} {negate_verb_phrase(prop)}",
                f"{entity.capitalize()} er et unntak"
            ]
        else:
            distractors = [
                f"De fleste {category_pl} {prop}",
                f"{entity.capitalize()} {prop} sannsynligvis"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "quantifier_all"
        }
    
    def generate_quantifier_none(self, op_type: dict) -> dict:
        """No X have Y. Z is X. Therefore Z does NOT have Y."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["eksempel"])
        
        category = theme
        category_pl = pluralize_category(category)
        entity = random.choice(theme_entities)
        prop = self._get_random_property_phrase(theme)
        
        statement = self._with_preface(
            f"Ingen {category_pl} {prop}.\n{entity.capitalize()} er et {category}."
        )
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva gjelder for dette vesenet?",
                "Hva følger logisk?",
                "Hvilken slutning er riktig?",
            ],
            extra=[
                "Hva er det vi helt sikkert IKKE får?",
                "Hva forsvinner fra mulighets-boksen?",
            ],
        )
        
        correct = f"{entity.capitalize()} {negate_verb_phrase(prop)}"
        
        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {prop}",
                f"{entity.capitalize()} er et unntak"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{entity.capitalize()} kanskje {prop}",
                f"Noen {category_pl} {prop}"
            ]
        else:
            distractors = [
                f"{entity.capitalize()} kan være et unntak",
                f"Det finnes {category_pl} som {prop}"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "quantifier_none"
        }
    
    def generate_exception(self, op_type: dict) -> dict:
        """Exception rule with explicit negation for the exception.

        Natural language like "alle X ... unntatt Y" is logically ambiguous.
        To keep the quiz strictly logical, we explicitly state what happens with Y.
        """
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["X", "Y"])
        
        category = theme
        category_pl = pluralize_category(category)
        prop = self._get_random_property_phrase(theme)
        
        if len(theme_entities) >= 2:
            exception, regular = random.sample(theme_entities, 2)
        else:
            exception, regular = "unntak", "vanlig"
        
        statement = self._with_preface(
            f"Alle {category_pl} {prop}, bortsett fra {exception}.\n"
            f"{exception.capitalize()} {negate_verb_phrase(prop)}."
        )
        question = self._pick_question(
            [
                f"Hva vet vi om {exception}?",
                f"Hva skjer med {exception}, da?",
            ],
            extra=[
                f"Hva er den rare sannheten om {exception}?",
                f"Hva kan {exception} IKKE slippe unna?",
            ],
        )
        
        correct = f"{exception.capitalize()} {negate_verb_phrase(prop)}"
        
        if self.difficulty == 1:
            distractors = [
                f"{exception.capitalize()} {prop}",
                f"Alle {category_pl} {prop}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{exception.capitalize()} kanskje {prop}",
                f"Alle {category_pl} {prop}"
            ]
        else:
            distractors = [
                f"{exception.capitalize()} {prop} noen ganger",
                f"{exception.capitalize()} er ikke et {category}"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "exception"
        }

    def generate_exception_heuristic(self, op_type: dict) -> dict:
        """Heuristic task: how "except" is commonly interpreted in everyday language.

        This is intentionally *not* strict logic. It trains pragmatic inference:
        many people usually understand "Alle X P, unntatt Y" as suggesting Y does not have P.
        """
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["X", "Y"])

        category = theme
        category_pl = pluralize_category(category)
        prop = self._get_random_property_phrase(theme)

        if len(theme_entities) >= 2:
            exception, _regular = random.sample(theme_entities, 2)
        else:
            exception = "unntak"

        statement = self._with_preface(f"Alle {category_pl} {prop}, unntatt {exception}.")
        question = self._pick_question(
            [
                f"I vanlig språk, hva tror folk oftest om {exception}?",
                f"Hvordan pleier man å forstå {exception} her?",
                f"Hva er den mest sannsynlige tolkningen om {exception}?",
            ],
            extra=[
                "Dette er språk-sanse-oppgave, ikke super-streng matematikk.",
            ],
        )

        correct = (
            f"I vanlig språk betyr det ofte at {exception.capitalize()} {negate_verb_phrase(prop)}"
        )

        if self.difficulty == 1:
            distractors = [
                f"I vanlig språk betyr det ofte at {exception.capitalize()} {prop}",
                "Strengt logisk kan vi ikke være helt sikre",
            ]
        elif self.difficulty == 2:
            distractors = [
                "Strengt logisk kan vi ikke være helt sikre",
                f"Det kan også bety at {exception.capitalize()} ikke er et {category}",
            ]
        else:
            distractors = [
                f"Det følger logisk helt sikkert at {exception.capitalize()} {negate_verb_phrase(prop)}",
                "Strengt logisk kan vi ikke være helt sikre",
            ]

        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "exception_heuristic",
        }

    def generate_incompatibility(self, op_type: dict) -> dict:
        """Incompatibility: A → ¬B.

        Follow the same pattern as Modus Ponens, but with a negated consequent.
        Uses config-driven properties (predicates) instead of class-words.
        """
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)

        statement = self._with_preface(
            (
                f"Hvis {entity} {prop_a}, så {entity} {negate_verb_phrase(prop_b)}.\n"
                f"{entity.capitalize()} {prop_a}."
            )
        )
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva følger av dette?",
                "Hva vet vi om den andre egenskapen?",
                "Hva kan vi utlede?",
            ],
            extra=[
                "Hva blir FORBUDT nå?",
                "Hva kan ikke skje samtidig her?",
                "Hva sier regelen når den er litt streng?",
            ],
        )

        correct = f"{entity.capitalize()} {negate_verb_phrase(prop_b)}"

        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {prop_b}",
                f"{entity.capitalize()} {prop_a} og {prop_b}",
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{entity.capitalize()} {negate_verb_phrase(prop_a)}",
                f"{entity.capitalize()} kanskje {prop_b}",
            ]
        else:
            distractors = [
                f"{entity.capitalize()} kanskje {prop_b}",
                f"{entity.capitalize()} {prop_a} og {prop_b}",
            ]

        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "incompatibility",
        }

    def generate_class_membership(self, op_type: dict) -> dict:
        """Class membership: infer that an individual belongs to a class.

        Uses the standard implication form: If P(x) then x is a B. P(a). Therefore a is a B.
        (This matches the overall quiz style and keeps everything config-driven.)
        """
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "romvesen"
        category = theme
        category_pl = pluralize_category(category)

        prop = self._get_random_property_phrase(theme)
        individual = self._get_random_individual_name(forbidden={category})

        statement = self._with_preface(
            f"Hvis {individual} {prop}, så er {individual} et {category}.\n{individual} {prop}."
        )
        question = self._pick_question(
            [
                "Hva kan vi konkludere?",
                "Hva følger av premissene?",
                "Hvilken slutning kan vi trekke?",
                "Hva vet vi nå om dette vesenet?",
            ],
            extra=[
                f"Hvilken boks må {individual} havne i?",
                "Hva sier klassifiserings-gnomen?",
            ],
        )

        correct = f"{individual} er et {category}"

        if self.difficulty == 1:
            distractors = [
                f"{individual} er ikke et {category}",
                f"Alle som {prop} er {category_pl}",
            ]
        elif self.difficulty == 2:
            distractors = [
                f"Alle {category_pl} {prop}",
                f"{individual} kanskje er et {category}",
            ]
        else:
            distractors = [
                f"Hvis {individual} er et {category}, så {individual} {prop}",
                f"{individual} kan være et {category} noen ganger",
            ]

        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "class_membership",
        }

    def generate_subclass(self, op_type: dict) -> dict:
        """Subclass: A ⊂ B.

        Kept in the same inferential format as quantifier tasks:
        All A are B. x is an A. Therefore x is a B.
        """
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "folkevesen"
        subclass_name = theme

        # Get super-class from config, fallback to "vesen"
        super_class_map = self.config.get("super_class", {})
        super_class = super_class_map.get(subclass_name, "vesen")

        subclass_pl = pluralize_category(subclass_name)
        super_class_pl = pluralize_category(super_class)

        theme_entities = self.entities.get(theme, ["X"])
        entity = random.choice(theme_entities)

        statement = self._with_preface(
            f"Alle {subclass_pl} er {super_class_pl}.\n{entity.capitalize()} er et {subclass_name}."
        )
        question = self._pick_question(
            [
                "Hva følger?",
                "Hva kan vi si om dette vesenet?",
                "Hvilken gruppe tilhører dette vesenet da?",
                "Hva vet vi nå?",
            ],
            extra=[
                "Hvilken super-gruppe blir dette, helt automatisk?",
                "Hvis vi putter det i en boks: hvilken boks?",
            ],
        )

        correct = f"{entity.capitalize()} er et {super_class}"

        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} er ikke et {super_class}",
                f"Alle {super_class_pl} er {subclass_pl}",
            ]
        elif self.difficulty == 2:
            distractors = [
                f"Alle {super_class_pl} er {subclass_pl}",
                "Vi kan ikke konkludere noe sikkert",
            ]
        else:
            distractors = [
                f"De fleste {subclass_pl} er {super_class_pl}",
                f"{entity.capitalize()} er et unntak",
            ]

        # If the question asks for group membership, keep all options in the same format
        # (statements about the specific entity), not global set statements.
        if "Hvilken gruppe" in question:
            sanitized: list[str] = []
            for d in distractors:
                if d.startswith("Alle ") or d.startswith("De fleste "):
                    continue
                sanitized.append(d)

            fallbacks = [
                f"{entity.capitalize()} er ikke et {super_class}",
                f"Vi kan ikke vite om {entity.capitalize()} er et {super_class}",
                "Vi kan ikke konkludere noe sikkert",
                f"{entity.capitalize()} er et unntak",
            ]
            for fb in fallbacks:
                if fb != correct and fb not in sanitized:
                    sanitized.append(fb)
                if len(sanitized) >= 2:
                    break

            distractors = sanitized

        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "subclass",
        }
    
    def generate_affirming_consequent_trap(self, op_type: dict) -> dict:
        """Trap: If A then B. B is true. We CANNOT conclude A (fallacy detection)."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        statement = self._with_preface(
            f"Hvis {entity} {prop_a}, så {entity} {prop_b}.\n{entity.capitalize()} {prop_b}."
        )
        question = self._pick_question(
            [
                "Hva følger nødvendigvis av dette?",
                "Kan vi trekke en sikker slutning her?",
                "Hva kan vi si med sikkerhet?",
                "Er det noe vi kan fastslå?",
            ],
            extra=[
                "Er dette en logikk-felle? Hva vet vi egentlig?",
                "Hva er det tryggeste vi kan si uten å gjette?",
            ],
        )
        
        # All answers same logical type: "Det følger at..." / "Det følger ikke at..."
        correct = f"Det følger ikke at {entity} {prop_a}"
        
        if self.difficulty == 1:
            distractors = [
                f"Det følger at {entity} {prop_a}",  # The fallacy!
                f"Det følger at {entity} {negate_verb_phrase(prop_a)}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"Det følger at {entity} {prop_a}",  # The fallacy!
                f"Det følger at {entity} {prop_a} og {prop_b}"
            ]
        else:
            distractors = [
                f"Det følger at {entity} {modalize('må', prop_a)}",  # Strong fallacy
                f"Det følger at hvis {entity} {prop_b}, så {entity} {prop_a}"  # Inverse fallacy
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "affirming_consequent_trap"
        }
    
    def generate_denying_antecedent_trap(self, op_type: dict) -> dict:
        """Trap: If A then B. A is false. We CANNOT conclude not-B (fallacy detection)."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        # Norwegian V2: "Hvis X gjør A, så gjør X også B"
        statement = self._with_preface(
            f"Hvis {entity} {prop_a}, så {entity} {prop_b}.\n{entity.capitalize()} {negate_verb_phrase(prop_a)}."
        )
        question = self._pick_question(
            [
                "Hva følger nødvendigvis av dette?",
                "Kan vi trekke en sikker slutning her?",
                "Hva kan vi si med sikkerhet?",
                "Er det noe vi kan fastslå?",
            ],
            extra=[
                "Prøver regelen å lure oss nå?",
                "Hva kan vi si uten å falle i fella?",
            ],
        )
        
        # All answers same logical type: "Det følger at..." / "Det følger ikke at..."
        correct = f"Det følger ikke noe sikkert om {entity} {prop_b}"
        
        if self.difficulty == 1:
            distractors = [
                f"Det følger at {entity} {negate_verb_phrase(prop_b)}",  # The fallacy!
                f"Det følger at {entity} {prop_b}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"Det følger at {entity} {negate_verb_phrase(prop_b)}",  # The fallacy!
                f"Det følger at regelen ikke gjelder"
            ]
        else:
            distractors = [
                f"Det følger at {entity} sannsynligvis {negate_verb_phrase(prop_b)}",
                f"Det følger at hvis {entity} {negate_leddsetning(prop_a)}, så {entity} {negate_verb_phrase(prop_b)}"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "denying_antecedent_trap"
        }

    def generate_de_morgan(self, op_type: dict) -> dict:
        """De Morgan's laws: ¬(A ∧ B) ⇔ (¬A ∨ ¬B)"""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        # Choose variant: negate conjunction or negate disjunction
        variant = random.choice(["conj_to_disj", "disj_to_conj"])
        
        q_pool = [
            "Hva betyr dette?",
            "Hva innebærer denne påstanden?",
            "Hvordan kan vi si det enklere?",
            "Hva følger logisk av dette?",
        ]
        if variant == "conj_to_disj":
            statement = self._with_preface(f"Det er ikke sant at {entity} både {prop_a} og {prop_b}.")
            question = self._pick_question(
                q_pool,
                extra=[
                    "Hvordan sier vi dette som en 'enten/eller'-greie?",
                    "Hvis en muffins oversetter dette, hva sier den?",
                ],
            )
            correct = f"{entity.capitalize()} {negate_verb_phrase(prop_a)} eller {negate_verb_phrase(prop_b)}"
        else:
            statement = self._with_preface(f"Det er ikke sant at {entity} {prop_a} eller {prop_b}.")
            question = self._pick_question(
                q_pool,
                extra=[
                    "Hvordan sier vi dette som en 'og'-greie?",
                    "Hva ville en robot med pannekake-hjerne skrevet?",
                ],
            )
            correct = f"{entity.capitalize()} {negate_verb_phrase(prop_a)} og {negate_verb_phrase(prop_b)}"
        
        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {prop_a} og {prop_b}",
                f"{entity.capitalize()} {prop_a} eller {prop_b}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{entity.capitalize()} kanskje {prop_a}",
                f"{entity.capitalize()} {prop_a} men ikke {prop_b}"
            ]
        else:
            distractors = [
                f"{entity.capitalize()} verken {prop_a} eller {prop_b}" if variant == "conj_to_disj" else f"{entity.capitalize()} {prop_a} eller {prop_b}",
                f"Minst én av egenskapene er sann"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "de_morgan"
        }

    def generate_temporal_always(self, op_type: dict) -> dict:
        """Temporal universal: Something ALWAYS happens. Therefore at time T it happens."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["eksempel"])
        
        subject = random.choice(theme_entities)
        prop = self._get_random_property_phrase(theme)
        
        # Insert "alltid" after the verb
        prop_parts = prop.split(' ', 1)
        if len(prop_parts) > 1:
            prop_alltid = f"{prop_parts[0]} alltid {prop_parts[1]}"
        else:
            prop_alltid = f"{prop} alltid"
        statement = self._with_preface(f"{subject.capitalize()} {prop_alltid}.")
        question = self._pick_question(
            [
                "Hva skjer i morgen?",
                "Hva skjer neste gang?",
                "Hva vil skje om en uke?",
                "Gjelder dette også i fremtiden?",
            ],
            extra=[
                "Hvis tiden hopper, hva skjer da?",
                "Hva skjer neste tirsdag i pannekake-universet?",
            ],
        )
        
        correct = f"{subject.capitalize()} {prop}"
        
        if self.difficulty == 1:
            distractors = [
                f"{subject.capitalize()} {negate_verb_phrase(prop)}",
                f"{subject.capitalize()} {prop} kanskje"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{subject.capitalize()} {prop} kanskje",
                f"{subject.capitalize()} {prop} noen ganger"
            ]
        else:
            distractors = [
                f"{subject.capitalize()} {prop} vanligvis",
                f"Det kommer an på omstendighetene"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "temporal_always"
        }

    def generate_temporal_sometimes(self, op_type: dict) -> dict:
        """Temporal existential: Something SOMETIMES happens. Cannot conclude it happens at specific time."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        theme_entities = self.entities.get(theme, ["eksempel"])
        
        subject = random.choice(theme_entities)
        prop = self._get_random_property_phrase(theme)
        
        statement = self._with_preface(f"{subject.capitalize()} {prop} noen ganger.")
        question = self._pick_question(
            [
                "Hva skjer i morgen?",
                "Hva skjer neste gang?",
                "Vet vi hva som skjer i fremtiden?",
                "Kan vi forutsi hva som skjer?",
            ],
            extra=[
                "Kan vi spå fremtiden med en ostebolle?",
                "Er dette alltid, eller bare av og til-påfunn?",
            ],
        )
        
        correct = random.choice([
            "Det er umulig å si sikkert",
            "Vi kan ikke vite det på forhånd",
            f"Kanskje {subject} {prop}, kanskje ikke",
            "Noen ganger betyr ikke alltid",
        ])
        
        if self.difficulty == 1:
            distractors = [
                f"{subject.capitalize()} {prop}",
                f"{subject.capitalize()} {negate_verb_phrase(prop)}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{subject.capitalize()} {prop} alltid",
                f"{subject.capitalize()} {prop} sannsynligvis"
            ]
        else:
            distractors = [
                f"{subject.capitalize()} {prop} mest sannsynlig",
                f"Det er 50% sjanse for at {subject} {prop}"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "temporal_sometimes"
        }

    def generate_contradiction(self, op_type: dict) -> dict:
        """Contradiction detection: A ∧ ¬A is impossible."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        statement = self._with_preface(
            f"{entity.capitalize()} {prop_a}.\n{entity.capitalize()} {negate_verb_phrase(prop_a)}."
        )
        question = self._pick_question(
            [
                "Hva kan vi si om disse påstandene?",
                "Kan begge påstandene stemme?",
                "Hva er problemet med disse utsagnene?",
                "Hva legger du merke til her?",
            ],
            extra=[
                "Er dette en logikk-kollisjon?",
                "Hører du at det knirker i sannheten?",
            ],
        )
        
        correct = random.choice([
            "Påstandene motsier hverandre – begge kan ikke være sanne",
            f"{entity.capitalize()} kan ikke både {to_infinitiv(prop_a)} og {to_infinitiv(negate_verb_phrase(prop_a))} samtidig",
            "Her er en selvmotsigelse – noe er galt",
            "Minst én av påstandene må være usann",
        ])
        
        if self.difficulty == 1:
            distractors = [
                "Begge påstandene kan godt være sanne",
                f"{entity.capitalize()} {prop_a} noen ganger"
            ]
        elif self.difficulty == 2:
            distractors = [
                "Den første påstanden er mest sannsynlig riktig",
                "Vi trenger å spørre noen for å finne ut"
            ]
        else:
            distractors = [
                "Avhengig av kontekst kan begge stemme",
                f"Det kan være at {entity} {prop_a} i noen tilfeller"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "contradiction"
        }

    def generate_possibility_implication(self, op_type: dict) -> dict:
        """Modal possibility: If A then MAYBE B. A is true. We cannot be certain about B."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        subject_name = entity.capitalize()
        
        # Modal markers for "possibly" (clauses that keep finite verb form)
        modal_markers = [
            "kan det hende at",
            "kan det være at",
            "det er mulig at",
        ]
        modal = random.choice(modal_markers)
        
        statement = self._with_preface(
            (
                f"Hvis {subject_name} {prop_a}, {modal} {subject_name} vil {to_infinitiv(prop_b)}.\n"
                f"{subject_name} {prop_a} nå."
            )
        )
        question = self._pick_question(
            [
                f"Hva kan vi forutsi om at {subject_name} vil {to_infinitiv(prop_b)}?",
                f"Er {subject_name} garantert å {to_infinitiv(prop_b)}, eller bare kanskje?",
            ],
            extra=[
                "Er dette en sikker spådom, eller bare en kanskje-kjeks?",
                "Kan vi være helt sikre, eller bare litt sikre?",
            ],
        )
        
        # Correct: probabilistic uncertainty phrasing (keep it short and child-friendly)
        correct_variants = [
            "Det er mulig, men ikke sikkert",
            "Kanskje, men vi kan ikke vite sikkert",
            "Det kan skje, men vi vet ikke sikkert",
            "Mulig, men ikke sikkert",
            "Vi kan ikke være sikre",
        ]
        correct = random.choice(correct_variants)
        
        if self.difficulty == 1:
            distractors = [
                f"{entity.capitalize()} {prop_b}",  # Treating possibility as certainty
                f"{entity.capitalize()} {negate_verb_phrase(prop_b)}"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"{entity.capitalize()} {prop_b} helt sikkert",
                f"{entity.capitalize()} {prop_b} aldri"
            ]
        else:
            distractors = [
                f"{entity.capitalize()} {modalize('må', prop_b)}",  # Necessity fallacy
                f"Det er umulig at {entity} {prop_b}"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "possibility_implication"
        }

    def generate_excluded_middle(self, op_type: dict) -> dict:
        """Law of excluded middle: P ∨ ¬P. No third option exists."""
        themes = list(self.entities.keys())
        theme = random.choice(themes) if themes else "dyr"
        entity, prop_a, prop_b = self._get_random_entity_and_properties(theme)
        
        statement = f"Enten {entity} {prop_a}, eller {entity} {negate_verb_phrase(prop_a)}."
        question = random.choice([
            "Finnes det en tredje mulighet?",
            "Er det noen annen mulighet her?",
            "Kan det finnes et mellomvalg?",
            f"Har {entity} flere alternativer?",
        ])
        
        correct = random.choice([
            "Nei, det er enten det ene eller det andre",
            f"{entity.capitalize()} enten {prop_a} eller ikke – ingen mellomting",
            "Nei, det finnes bare to muligheter her",
            "Det er kun to utfall – ingen tredje vei",
        ])
        
        if self.difficulty == 1:
            distractors = [
                f"Ja, {entity} kan gjøre begge deler samtidig",
                "Ja, det kan være ingen av dem"
            ]
        elif self.difficulty == 2:
            distractors = [
                f"Ja, {entity} kan gjøre litt av begge deler",
                "Det kommer an på når vi spør"
            ]
        else:
            distractors = [
                "I visse tilfeller kan logikken bøyes",
                f"{entity.capitalize()} kan ha en mellomtilstand"
            ]
        
        options = shuffle_list([correct] + distractors[:2])
        return {
            "statement": statement,
            "question": question,
            "options": options,
            "correct": options.index(correct),
            "type": "excluded_middle"
        }
    
    def generate_question(self, op_type_id: str) -> dict:
        """Generate question by operation type ID"""
        op_type = next((ot for ot in self.operation_types if ot["id"] == op_type_id), None)
        if not op_type:
            print(f"[ERROR] Operation type '{op_type_id}' not found in config!")
            return {}
        
        generators = {
            "modus_ponens": self.generate_modus_ponens,
            "modus_tollens": self.generate_modus_tollens,
            "universal_instantiation": self.generate_universal_instantiation,
            "disjunctive_syllogism": self.generate_disjunctive_syllogism,
            "hypothetical_syllogism": self.generate_hypothetical_syllogism,
            "contraposition": self.generate_contraposition,
            "existential_instantiation": self.generate_existential_instantiation,
            "negation_introduction": self.generate_negation_introduction,
            "insufficient_info": self.generate_insufficient_info,
            # New operation types
            "conjunction": self.generate_conjunction,
            "disjunction_incl": self.generate_disjunction_incl,
            "disjunction_excl": self.generate_disjunction_excl,
            "double_negation": self.generate_double_negation,
            "quantifier_all": self.generate_quantifier_all,
            "quantifier_none": self.generate_quantifier_none,
            "exception": self.generate_exception,
            "affirming_consequent_trap": self.generate_affirming_consequent_trap,
            "denying_antecedent_trap": self.generate_denying_antecedent_trap,
            # Spec completion types
            "de_morgan": self.generate_de_morgan,
            "temporal_always": self.generate_temporal_always,
            "temporal_sometimes": self.generate_temporal_sometimes,
            "contradiction": self.generate_contradiction,
            "excluded_middle": self.generate_excluded_middle,
            # Spec additions (not previously in JSON)
            "incompatibility": self.generate_incompatibility,
            "class_membership": self.generate_class_membership,
            "subclass": self.generate_subclass,
            # Modal logic
            "possibility_implication": self.generate_possibility_implication,
        }
        
        generator = generators.get(op_type_id)
        if not generator:
            print(f"[ERROR] No generator function for type '{op_type_id}'!")
            return {}
        
        question = generator(op_type)
        
        # VALIDATE: Check question structure
        required_keys = ["statement", "question", "options", "correct", "type"]
        missing_keys = [key for key in required_keys if key not in question]
        
        if missing_keys:
            print(f"[ERROR] Generator '{op_type_id}' returned incomplete question! Missing keys: {missing_keys}")
            return {}
        
        # VALIDATE: Check options count (should be 3 for LogikkQuiz)
        if not isinstance(question["options"], list) or len(question["options"]) < 2:
            print(f"[ERROR] Generator '{op_type_id}' returned invalid options: {question.get('options')}")
            return {}
        
        return question
    
    def generate_quiz(self, count: int) -> list:
        """Generate session with variety of logic operations"""
        available_types = [ot["id"] for ot in self.operation_types]
        
        # Filter by difficulty (insufficient_info only at level 2+)
        if self.difficulty < 2:
            available_types = [t for t in available_types if t != "insufficient_info"]
        
        if not available_types or count <= 0:
            return []
        
        selected_type_ids: list[str] = []
        
        # Ensure variety: pick each type once before repeating
        while len(selected_type_ids) < count:
            shuffled = shuffle_list(available_types)
            for type_id in shuffled:
                if len(selected_type_ids) >= count:
                    break
                selected_type_ids.append(type_id)
        
        random.shuffle(selected_type_ids)
        
        questions: list[dict] = []
        for type_id in selected_type_ids:
            question = self.generate_question(type_id)
            if question and isinstance(question, dict) and "statement" in question:
                questions.append(question)
            else:
                print(f"[WARNING] Skipped invalid question from '{type_id}' generator")
        
        return questions


class LogikkQuizApp(BaseQuizWidget):
    """Main quiz widget for LogikkQuiz logic quiz"""
    
    def __init__(self):
        super().__init__(config_filename="app_logikkquiz.json")
        
        # Load system version for StatusBar
        try:
            main_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "main.json")
            with open(main_path, encoding="utf-8") as f:
                main_data = json.load(f)
            self.system_version = f"v{main_data.get('system', {}).get('version', '0.0.0')}"
        except Exception:
            self.system_version = ""
        
        self.status_default = self.config.get("texts", {}).get("status_default", "LogikkQuiz")
        self.status_bar: Optional[StatusBar] = None
        
        # Game state
        self.questions = []
        self.current_question_index = 0
        self.answers: list = []
        self.results: list = []
        self.analytics_logged: list[bool] = []
        self.total_questions = self.config.get("game", {}).get("total_questions", 10)
        self.answer_count = self.config.get("game", {}).get("answer_count", 3)  # 3 for logic quiz
        self.game_session_start_ts: float = 0.0
        self.settings_frame: QWidget | None = None
        self.stats_modal_frame: QWidget | None = None
        self.stats_modal_content: LogikkQuizStatsModal | None = None
        self.questions_control: Optional[SettingControl] = None
        self.difficulty_control: Optional[SettingControl] = None
        self.saveclose_button: Optional[SaveCloseButton] = None
        self.saveclose_wrapper: Optional[QWidget] = None
        self._intro_mode: str = "intro"
        self._settings_return_mode: str = "intro"
        self._settings_icons_visible: bool = False
        
        self.setup_ui()
        
        assert self.intro_widget is not None
        assert self.game_widget is not None
        assert self.service_buttons_toolbar is not None
        
        self.intro_widget: QWidget
        self.game_widget: QWidget
        self.service_buttons_toolbar: ServiceButtonsToolbar
    
    def setup_ui(self):
        """Setup the quiz user interface"""
        bg_color = self.config.get("ui", {}).get("background_color", "#D8DFE5")
        self.setStyleSheet(f"background-color: {bg_color};")
        
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Intro screen
        self.intro_widget = QWidget()
        intro_layout = QVBoxLayout(self.intro_widget)
        intro_layout.setContentsMargins(0, 0, 0, 0)
        intro_layout.setSpacing(20)
        intro_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        intro_content = QWidget()
        intro_content_layout = QVBoxLayout(intro_content)
        intro_content_layout.setContentsMargins(100, 100, 100, 100)
        intro_content_layout.setSpacing(20)
        intro_content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        texts_cfg = self.config.get("texts", {})
        title_text = texts_cfg.get("intro_title") or texts_cfg.get("title") or "LOGIKKQUIZ"
        subtitle_text = texts_cfg.get("intro_subtitle") or ""
        header_widget, self.intro_title_block = self.create_intro_header_block(
            title=title_text,
            subtitle=subtitle_text,
            parent=self
        )
        self.register_intro_header_widget(header_widget, self.intro_widget)
        intro_layout.addStretch(1)
        
        intro_content_layout.addStretch(2)
        intro_text = self.config.get("texts", {}).get("intro", "").format(questions=self.total_questions)
        self.intro_label = QLabel(intro_text)
        intro_size = self.config.get("fonts", {}).get("intro_size", 42)
        self.intro_label.setFont(create_font_px(FONT_NAME, intro_size))
        text_color = self.config.get("ui", {}).get("text_color", "#2C3E50")
        self.intro_label.setStyleSheet(f"color: {text_color}; line-height: 150%;")
        self.intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.intro_label.setWordWrap(True)
        intro_content_layout.addWidget(self.intro_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        intro_content_layout.addSpacing(20)
        
        # Icons row container (for results display)
        self.icons_container = QWidget()
        self.icons_layout = QHBoxLayout(self.icons_container)
        self.icons_layout.setContentsMargins(0, 0, 0, 0)
        self.icons_layout.setSpacing(10)
        self.icons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_content_layout.addWidget(self.icons_container, alignment=Qt.AlignmentFlag.AlignCenter)
        self.icons_container.hide()
        
        intro_content_layout.addSpacing(40)
        
        # Start button
        self.start_button = PlayButton(self.start_game, UI_CONFIG, parent=self)
        intro_content_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # SaveClose button for results
        self.saveclose_button = SaveCloseButton(self._handle_results_saveclose, UI_CONFIG, parent=self)
        self.saveclose_wrapper = self.saveclose_button.get_wrapper()
        intro_content_layout.addWidget(self.saveclose_wrapper, alignment=Qt.AlignmentFlag.AlignCenter)
        self.saveclose_wrapper.hide()
        
        intro_content_layout.addStretch(2)
        intro_layout.addWidget(intro_content, alignment=Qt.AlignmentFlag.AlignCenter)
        intro_layout.addStretch(1)
        
        container_layout.addWidget(self.intro_widget)
        
        # Game screen
        self.game_widget = QWidget()
        self.game_widget.hide()
        self.setup_game_ui()
        container_layout.addWidget(self.game_widget)
        
        # StatusBar
        self.status_bar = StatusBar(self.ui_config, default_left=self.status_default, version_text=self.system_version)
        container_layout.addWidget(self.status_bar)
        self._update_statusbar_utilons(force_reload=True)
        
        # Setup service buttons
        self.setup_service_buttons()
        self._toggle_intro_cta(show_saveclose=False)
    
    def setup_game_ui(self):
        """Setup game screen UI - similar to MatteQuiz but with 3 answer buttons"""
        game_layout = QVBoxLayout(self.game_widget)
        game_layout.setContentsMargins(50, 70, 50, 30)
        game_layout.setSpacing(15)
        
        text_color = self.config.get("ui", {}).get("text_color", "#2C3E50")
        
        # Progress indicator
        self.progress_label = QLabel()
        progress_size = self.config.get("fonts", {}).get("progress_size", 24)
        self.progress_label.setFont(create_font_px(FONT_NAME, progress_size, QFont.Weight.Bold))
        self.progress_label.setStyleSheet(f"color: {text_color};")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        game_layout.addWidget(self.progress_label)
        
        game_layout.addSpacing(10)
        
        # Question container (statement + question merged)
        question_container = QWidget()
        question_container_layout = QHBoxLayout(question_container)
        question_container_layout.setContentsMargins(0, 0, 0, 0)
        question_container_layout.addStretch(1)
        
        self.question_label = QLabel()
        question_size = self.config.get("fonts", {}).get("question_size", 32)
        self.question_label.setFont(create_font_px(FONT_NAME, question_size, QFont.Weight.Bold))
        self.question_label.setStyleSheet(f"""
            color: {text_color};
            background-color: white;
            border: 2px solid {self.config.get('ui', {}).get('border_color', '#6C757D')};
            border-radius: 15px;
            padding: 25px;
        """)
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setWordWrap(True)
        self.question_label.setMinimumHeight(120)
        question_container_layout.addWidget(self.question_label, 4)
        question_container_layout.addStretch(1)
        game_layout.addWidget(question_container)
        self.question_container = question_container  # Store reference for width calculation
        
        game_layout.addSpacing(15)
        
        # Answer buttons container (3 buttons for logic quiz)
        self.answer_buttons_widget = QWidget()
        answer_container_layout = QHBoxLayout(self.answer_buttons_widget)
        answer_container_layout.setContentsMargins(0, 0, 0, 0)
        answer_container_layout.addStretch(3)
        
        answer_column_widget = QWidget()
        answer_column = QVBoxLayout(answer_column_widget)
        option_spacing = self.config.get("ui", {}).get("option_spacing", 35)
        answer_column.setSpacing(option_spacing)
        
        option_min_height = self.config.get("ui", {}).get("option_min_height", 100)
        
        self.answer_buttons = []
        for i in range(self.answer_count):  # 3 buttons
            btn = QPushButton()
            answer_size = self.config.get("fonts", {}).get("answer_size", 28)
            btn.setFont(create_font_px(FONT_NAME, answer_size))
            btn.setMinimumHeight(option_min_height)
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.config.get('ui', {}).get('button_color', '#E9ECEF')};
                    border: 2px solid {self.config.get('ui', {}).get('border_color', '#6C757D')};
                    border-radius: 15px;
                    color: {text_color};
                    padding: 15px;
                }}
                QPushButton:hover {{
                    background-color: {self.config.get('ui', {}).get('hover_color', '#b3cfff')};
                    font-weight: bold;
                }}
            """)
            btn.clicked.connect(lambda checked, idx=i: self.answer_selected(idx))
            self.answer_buttons.append(btn)
            answer_column.addWidget(btn)
        
        self.answer_column_widget = answer_column_widget  # Store reference
        answer_container_layout.addWidget(answer_column_widget, 2)
        answer_container_layout.addStretch(3)
        game_layout.addWidget(self.answer_buttons_widget)
        
        game_layout.addStretch(1)
        
        # Next button
        self.next_button = PlayButton(self.next_question, UI_CONFIG, icon_name="btn_next.png", parent=self)
        self.next_button.setEnabled(True)
        self.next_button.hide()
        game_layout.addWidget(self.next_button, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def setup_service_buttons(self):
        """Setup service buttons"""
        buttons = [
            {'name': 'stats', 'callback': self.open_stats_panel},
            {'name': 'settings', 'callback': self.show_settings},
            {'name': 'back', 'callback': self.back_from_game},
            {'name': 'home', 'callback': self.go_home}
        ]
        self.setup_service_buttons_base(buttons)
        self.show_intro_buttons()

    def open_stats_panel(self) -> None:
        """Open stats modal overlay."""
        if self._stats_modal_visible():
            # Already open - just refresh
            if self.stats_modal_content:
                module_stats, daily_stats = self._load_all_stats()
                self.stats_modal_content.refresh(module_stats, daily_stats)
            return

        # Get config
        stats_modal_cfg = (self.ui_config.get('containers', {}) or {}).get('stats_modal', {})
        overlay_color = (stats_modal_cfg.get('overlay', {}) or {}).get('color')
        self._show_settings_overlay(color=overlay_color)

        # Create modal frame
        self.stats_modal_frame = self.create_modal_frame('stats_modal')

        frame_cfg = stats_modal_cfg.get('frame', {}) if isinstance(stats_modal_cfg, dict) else {}
        margins = frame_cfg.get('margins', {}) if isinstance(frame_cfg, dict) else {}
        spacing = frame_cfg.get('spacing', 30)

        modal_layout = QVBoxLayout(self.stats_modal_frame)
        modal_layout.setContentsMargins(
            margins.get('left', 60),
            margins.get('top', 40),
            margins.get('right', 60),
            margins.get('bottom', 40)
        )
        modal_layout.setSpacing(spacing)

        # Get stats config from app config
        stats_config = self.config.get('stats', {})

        # Create stats modal content
        self.stats_modal_content = LogikkQuizStatsModal(
            stats_config,
            self.ui_config,
            parent=self.stats_modal_frame
        )
        modal_layout.addWidget(self.stats_modal_content)

        # Buttons row (only SaveClose, no Reset)
        from core.ui_components import SaveCloseButton
        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)

        stats_saveclose_btn = SaveCloseButton(self._close_stats_modal, self.ui_config, self)
        buttons_row.addWidget(stats_saveclose_btn.get_wrapper())

        buttons_row.addStretch(1)
        modal_layout.addLayout(buttons_row)

        # Load and display stats
        module_stats, daily_stats = self._load_all_stats()
        self.stats_modal_content.refresh(module_stats, daily_stats)

        # Show modal
        self.stats_modal_frame.show()
        self.stats_modal_frame.raise_()
        self.stats_modal_frame.setFocus()
        self.show_settings_buttons()

    def _stats_modal_visible(self) -> bool:
        """Check if stats modal is currently visible."""
        return self.stats_modal_frame is not None and self.stats_modal_frame.isVisible()

    def _load_all_stats(self) -> tuple:
        """Load both module stats and daily stats."""
        try:
            stats = stats_utils.load_stats()
            module_stats = stats.get('apps', {}).get('logikkquiz', {})
            daily_stats = stats.get('daily', {})
            return module_stats, daily_stats
        except Exception:
            return {}, {}

    def _close_stats_modal(self) -> None:
        """Close stats modal and restore previous screen."""
        if self.stats_modal_frame:
            self.stats_modal_frame.close()
            self.stats_modal_frame.deleteLater()
            self.stats_modal_frame = None
        self.stats_modal_content = None
        self._hide_settings_overlay()
        self._restore_toolbar_after_modal()

    def _restore_toolbar_after_modal(self) -> None:
        """Restore correct toolbar buttons based on current visible screen."""
        if self.intro_widget and self.intro_widget.isVisible():
            self.show_intro_buttons()
        elif self.game_widget and self.game_widget.isVisible():
            self.show_game_buttons()

    def _handle_results_saveclose(self):
        """Handle SaveClose tap from results screen"""
        self.go_home()

    def _toggle_intro_cta(self, show_saveclose: bool):
        """Switch between Play and SaveClose buttons"""
        if hasattr(self, 'start_button') and self.start_button:
            self.start_button.setVisible(not show_saveclose)
        if self.saveclose_wrapper is not None:
            self.saveclose_wrapper.setVisible(show_saveclose)
    
    def show_intro_buttons(self):
        """Show buttons for intro screen: stats + settings + home"""
        if hasattr(self, 'service_buttons_toolbar'):
            self.service_buttons_toolbar.show_button('stats')
            self.service_buttons_toolbar.show_button('settings')
            self.service_buttons_toolbar.hide_button('back')
            self.service_buttons_toolbar.show_button('home')
    
    def show_settings_buttons(self):
        """Show buttons for settings screen: back + home"""
        if hasattr(self, 'service_buttons_toolbar'):
            self.service_buttons_toolbar.hide_button('stats')
            self.service_buttons_toolbar.hide_button('settings')
            self.service_buttons_toolbar.show_button('back')
            self.service_buttons_toolbar.show_button('home')
    
    def show_game_buttons(self):
        """Show buttons for game screen: back + home"""
        if hasattr(self, 'service_buttons_toolbar'):
            self.service_buttons_toolbar.hide_button('stats')
            self.service_buttons_toolbar.hide_button('settings')
            self.service_buttons_toolbar.show_button('back')
            self.service_buttons_toolbar.show_button('home')
            self.service_buttons_toolbar.hide_button('settings')
            self.service_buttons_toolbar.show_button('back')
            self.service_buttons_toolbar.show_button('home')
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle ESC and Enter navigation"""
        if event.key() == Qt.Key.Key_Escape:
            if self.settings_frame is not None and self.settings_frame.isVisible():
                self.close_settings()
            elif self.game_widget.isVisible():
                self.game_widget.hide()
                self.intro_widget.show()
                self.show_intro_buttons()
            elif self.intro_widget.isVisible():
                self.go_home()
            else:
                self.go_home()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.game_widget.isVisible() and hasattr(self, 'next_button'):
                if self.next_button.isVisible() and self.next_button.isEnabled():
                    self.next_question()
        else:
            super().keyPressEvent(event)
    
    def _update_statusbar_utilons(self, force_reload: bool = False):
        """Update utilons display in StatusBar"""
        if self.status_bar is None:
            return
        utilons = 0
        try:
            from core.analytics import get_analytics
            analytics = get_analytics()
            if force_reload:
                analytics.reload_from_disk()
            utilons = int(analytics.get_today_utilons())
        except Exception as exc:
            print(f"[LogikkQuiz] Status utilon update failed: {exc}")
        self.status_bar.set_utilons(utilons)
    
    def go_home(self):
        """Return to launcher"""
        from core.analytics import get_analytics
        get_analytics().flush()
        
        self.questions = []
        self.current_question_index = 0
        self.answers = []
        self.results = []
        
        if hasattr(self, 'icons_container'):
            self.icons_container.hide()
        
        intro_text = self.config.get("texts", {}).get("intro", "").format(questions=self.total_questions)
        if hasattr(self, 'intro_label'):
            self.intro_label.setText(intro_text)
        self._toggle_intro_cta(show_saveclose=False)
        self._intro_mode = "intro"
        
        super().go_home()
    
    def show_settings(self):
        """Show PIN overlay then settings"""
        if not self.intro_widget.isVisible():
            return
        self.show_pin_overlay(self._show_settings_impl)
    
    def _show_settings_impl(self):
        """Show settings overlay"""
        if not self.intro_widget.isVisible():
            return
        
        self._show_settings_overlay()
        self._settings_return_mode = getattr(self, '_intro_mode', 'intro')
        self._settings_icons_visible = self.icons_container.isVisible() if hasattr(self, 'icons_container') else False
        self.icons_container.hide()
        
        self.settings_frame = self.create_settings_frame()
        
        settings_cfg = self.ui_config.get('containers', {}).get('settings', {})
        frame_cfg = settings_cfg.get('frame', {})
        margins = frame_cfg.get('margins', {})
        spacing = frame_cfg.get('spacing', 30)
        settings_layout = QVBoxLayout(self.settings_frame)
        settings_layout.setContentsMargins(
            int(margins.get('left', 40)),
            int(margins.get('top', 40)),
            int(margins.get('right', 40)),
            int(margins.get('bottom', 40))
        )
        settings_layout.setSpacing(spacing)
        
        title_label = SettingsTitleLabel(self.ui_config, self)
        settings_layout.addWidget(title_label)
        
        settings_layout.addStretch(1)
        
        def format_label_text(text: Optional[str], fallback: str) -> str:
            source = (text or fallback or "").strip()
            if not source:
                return ""
            lowered = source.lower()
            return lowered[0].upper() + lowered[1:]
        
        questions_label = format_label_text(
            self.config.get("texts", {}).get("settings_questions"),
            "ANTALL OPPGAVER"
        )
        self.questions_control = SettingControl(
            questions_label,
            self.total_questions,
            lambda delta: self.change_setting('questions', delta),
            self.ui_config,
            self.config,
            self,
        )
        settings_layout.addWidget(self.questions_control)

        current_difficulty = self.config.get("game", {}).get("difficulty_level", 1)
        difficulty_label = format_label_text(
            self.config.get("texts", {}).get("settings_difficulty"),
            "VANSKELIGHETSGRAD"
        )
        self.difficulty_control = SettingControl(
            difficulty_label,
            current_difficulty,
            lambda delta: self.change_setting('difficulty', delta),
            self.ui_config,
            self.config,
            self,
        )
        settings_layout.addWidget(self.difficulty_control)
        
        settings_layout.addStretch(2)
        
        buttons_container = QHBoxLayout()
        buttons_container.addStretch(1)
        saveclose_btn = SaveCloseButton(self.close_settings, self.ui_config, self)
        buttons_container.addWidget(saveclose_btn.get_wrapper())
        buttons_container.addStretch(1)
        settings_layout.addLayout(buttons_container)
        
        if hasattr(self, 'settings_overlay') and self.settings_overlay:
            self.settings_overlay.raise_()
        
        self.settings_frame.show()
        self.settings_frame.raise_()
        self.settings_frame.setFocus()
        
        self.show_settings_buttons()
    
    def change_setting(self, setting_name: str, delta: int):
        """Change and save setting"""
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "app_logikkquiz.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        ranges = self.config["game"].get("settings_ranges", {})
        
        if setting_name == 'questions':
            min_val = ranges.get("questions_min", 5)
            max_val = ranges.get("questions_max", 20)
            new_value = max(min_val, min(max_val, self.config["game"]["total_questions"] + delta))
            self.config["game"]["total_questions"] = new_value
            config["game"]["total_questions"] = new_value
            self.total_questions = new_value
            if self.questions_control:
                self.questions_control.set_value(new_value)
        elif setting_name == 'difficulty':
            min_val = ranges.get("difficulty_min", 1)
            max_val = ranges.get("difficulty_max", 3)
            new_value = max(min_val, min(max_val, self.config["game"]["difficulty_level"] + delta))
            self.config["game"]["difficulty_level"] = new_value
            config["game"]["difficulty_level"] = new_value
            if self.difficulty_control:
                self.difficulty_control.set_value(new_value)
        
        from core.atomic import atomic_save_json
        atomic_save_json(config_path, config)
    
    def close_settings(self):
        """Close settings frame"""
        return_mode = getattr(self, '_settings_return_mode', 'intro')
        icons_visible_before = getattr(self, '_settings_icons_visible', False)

        super().close_settings()

        if return_mode == 'results':
            if hasattr(self, 'icons_container') and icons_visible_before:
                self.icons_container.show()
            self._toggle_intro_cta(show_saveclose=True)
            self._intro_mode = 'results'
        else:
            if hasattr(self, 'icons_container'):
                self.icons_container.hide()
            self._toggle_intro_cta(show_saveclose=False)
            intro_text = self.config.get("texts", {}).get("intro", "").format(questions=self.total_questions)
            self.intro_label.setText(intro_text)
            self._intro_mode = 'intro'

        self._settings_return_mode = self._intro_mode
        self._settings_icons_visible = False
    
    def start_game(self):
        """Start new game session"""
        # Preload icons
        try:
            utilon_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "icons", "utilon.png")
            error_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "icons", "utilon-null.png")
            if os.path.exists(utilon_icon_path):
                _ = QPixmap(utilon_icon_path)
            if os.path.exists(error_icon_path):
                _ = QPixmap(error_icon_path)
        except Exception as e:
            print(f"[LogikkQuiz] Icon preload error: {e}")
        
        # Generate questions
        difficulty = self.config.get("game", {}).get("difficulty_level", 1)
        generator = LogicQuestionGenerator(self.config, difficulty)
        self.questions = generator.generate_quiz(self.total_questions)
        
        # Reset state
        self.current_question_index = 0
        self.answers = [None] * len(self.questions)
        self.results = [None] * len(self.questions)
        self.analytics_logged = [False] * len(self.questions)
        self.game_session_start_ts = time.time()
        
        self.icons_container.hide()
        
        if self.status_bar:
            self.status_bar.hide()
        
        self.intro_widget.hide()
        self.game_widget.show()
        self.show_game_buttons()
        
        self.load_question()
    
    def back_from_game(self):
        """Return from game to intro screen"""
        self.game_widget.hide()
        self.intro_widget.show()
        self.show_intro_buttons()
        
        if self.status_bar:
            self.status_bar.show()
        
        self.questions = []
        self.current_question_index = 0
        self.answers = []
        self.results = []
        self.analytics_logged = []
        
        self.icons_container.show()
        self._toggle_intro_cta(show_saveclose=False)
        self._intro_mode = "intro"
    
    def load_question(self):
        """Load current question into UI"""
        if self.current_question_index >= len(self.questions):
            self.show_results()
            return
        
        question = self.questions[self.current_question_index]
        
        if not isinstance(question, dict) or "statement" not in question:
            print(f"[ERROR] Invalid question at index {self.current_question_index}: {question}")
            self.current_question_index += 1
            self.load_question()
            return
        
        # Update progress
        progress_text = self.config.get("texts", {}).get("progress_template", "Oppgave {current}/{total}")
        self.progress_label.setText(progress_text.format(
            current=self.current_question_index + 1,
            total=len(self.questions)
        ))
        
        # Merge statement + question into one label (no quotes)
        statement_text = question["statement"]
        question_text = question["question"]
        combined_text = f"{statement_text}\n{question_text}"
        self.question_label.setText(combined_text)
        
        text_color = self.config.get("ui", {}).get("text_color", "#2C3E50")
        
        # Calculate min width for buttons (50% of question container width)
        min_width_percent = self.config.get("ui", {}).get("option_min_width_percent", 50)
        question_width = self.question_label.width() if self.question_label.width() > 0 else 600
        min_button_width = int(question_width * min_width_percent / 100)
        
        # Find max text width among all options
        # Extra padding: 80 for margins + 60 for checkmark icon = 140
        max_text_width = min_button_width
        font_metrics = self.answer_buttons[0].fontMetrics() if self.answer_buttons else None
        if font_metrics:
            for opt in question["options"]:
                text_width = font_metrics.horizontalAdvance(str(opt)) + 140  # padding + checkmark
                if text_width > max_text_width:
                    max_text_width = text_width
        
        # Set all buttons to max width
        for btn in self.answer_buttons:
            btn.setFixedWidth(max_text_width)
        
        # Update answer buttons
        for i, btn in enumerate(self.answer_buttons):
            if i < len(question["options"]):
                btn.setText(str(question["options"][i]))
                btn.setEnabled(True)
                btn.show()
                
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.config.get('ui', {}).get('button_color', '#E9ECEF')};
                        border: 2px solid {self.config.get('ui', {}).get('border_color', '#6C757D')};
                        border-radius: 15px;
                        color: {text_color};
                        padding: 15px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.config.get('ui', {}).get('hover_color', '#b3cfff')};
                        font-weight: bold;
                    }}
                """)
                
                if self.answers[self.current_question_index] is not None:
                    if i == self.answers[self.current_question_index]:
                        btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {self.config.get('ui', {}).get('hover_color', '#b3cfff')};
                                border: 3px solid {self.config.get('ui', {}).get('accent_color', '#007FFF')};
                                border-radius: 15px;
                                color: {text_color};
                                padding: 15px;
                                font-weight: bold;
                            }}
                        """)
            else:
                btn.hide()
        
        QApplication.processEvents()
        
        if self.answers[self.current_question_index] is not None:
            selected_idx = self.answers[self.current_question_index]
            if isinstance(selected_idx, int):
                self.show_answer_feedback(selected_idx)
        else:
            self.next_button.hide()
            self.next_button.setEnabled(False)
    
    def answer_selected(self, answer_index: int):
        """Handle answer selection"""
        if self.answers[self.current_question_index] is not None:
            return

        self.answers[self.current_question_index] = answer_index

        question = self.questions[self.current_question_index]
        is_correct = (answer_index == question["correct"])
        self.results[self.current_question_index] = is_correct
        
        self.show_answer_feedback(answer_index)
    
    def show_answer_feedback(self, selected_index: int):
        """Show feedback for selected answer"""
        question = self.questions[self.current_question_index]
        correct_index = question["correct"]
        text_color = self.config.get("ui", {}).get("text_color", "#2C3E50")
        
        for btn in self.answer_buttons:
            btn.setEnabled(False)
        
        correct_color = self.config.get("ui", {}).get("correct_color", "#90EE90")
        error_color = self.config.get("ui", {}).get("error_color", "#FFB6B6")
        
        def darken_color(hex_color: str) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r, g, b = int(r * 0.7), int(g * 0.7), int(b * 0.7)
            return f'#{r:02x}{g:02x}{b:02x}'
        
        correct_border = darken_color(correct_color)
        error_border = darken_color(error_color)
        
        for i, btn in enumerate(self.answer_buttons):
            if i >= len(question["options"]):
                continue
            
            original_text = str(question["options"][i])
            
            if i == correct_index:
                btn.setText(f"✅  {original_text}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {correct_color};
                        border: 3px solid {correct_border};
                        border-radius: 15px;
                        color: {text_color};
                        padding: 15px;
                        font-weight: bold;
                    }}
                """)
            elif i == selected_index:
                btn.setText(f"❌  {original_text}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {error_color};
                        border: 3px solid {error_border};
                        border-radius: 15px;
                        color: {text_color};
                        padding: 15px;
                    }}
                """)
        
        self.next_button.setEnabled(True)
        self.next_button.show()
        self.next_button.raise_()
    
    def _log_answer_once(self, question_index: int):
        """Sync a single question result to analytics"""
        if not self.results or question_index < 0 or question_index >= len(self.results):
            return
        if question_index >= len(self.analytics_logged):
            return
        if self.analytics_logged[question_index]:
            return
        result = self.results[question_index]
        if result is None:
            return

        try:
            self.record_answer(bool(result))
            self.analytics_logged[question_index] = True
        except Exception as e:
            print(f"[LogikkQuiz] record_answer error (q{question_index+1}): {e}")

    def next_question(self):
        """Load next question or show results"""
        self._log_answer_once(self.current_question_index)
        
        self.current_question_index += 1
        
        if self.current_question_index >= len(self.questions):
            self.show_results()
        else:
            self.load_question()
    
    def show_results(self):
        """Show results screen"""
        for idx in range(len(self.results)):
            self._log_answer_once(idx)
        
        score = sum(1 for r in self.results if r is True)
        total_questions = len(self.questions)

        session_seconds = int(time.time() - self.game_session_start_ts) if self.game_session_start_ts else 0

        # Bonuses
        result_cfg = self.config.get('result_screen', {}) or {}
        try:
            accuracy_bonus_amount = int(result_cfg.get('accuracy_bonus_utilons', 2))
        except Exception:
            accuracy_bonus_amount = 2
        accuracy_bonus = accuracy_bonus_amount if total_questions > 0 and score == total_questions else 0

        self._accuracy_bonus_utilons = int(accuracy_bonus)

        self.save_stats(score, total_questions, session_seconds=session_seconds)

        total_bonus = int(self._accuracy_bonus_utilons)
        if total_bonus > 0:
            self.add_utilons(total_bonus)
        
        result_text = f"Resultat: {score}/{total_questions}"
        self.intro_label.setText(result_text)
        
        # Clear previous icons
        while self.icons_layout.count():
            child = self.icons_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()
        
        MAX_ICONS = 20
        results_to_show = self.results[:MAX_ICONS]
        
        icon_size = 65
        utilon_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "icons", "utilon.png")
        error_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "icons", "utilon-null.png")
        
        total_icons = len(results_to_show)
        icons_per_row = total_icons if total_icons <= 11 else (total_icons + 1) // 2
        
        rows_container = QWidget()
        rows_layout = QVBoxLayout(rows_container)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(10)
        rows_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        current_row_layout = None
        for idx, result in enumerate(results_to_show):
            if idx % icons_per_row == 0:
                current_row = QWidget()
                current_row_layout = QHBoxLayout(current_row)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setSpacing(10)
                current_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                rows_layout.addWidget(current_row)
            
            icon_label = QLabel()
            icon_label.setFixedSize(icon_size, icon_size)
            icon_label.setScaledContents(True)
            
            if result:
                if os.path.exists(utilon_icon_path):
                    pixmap = QPixmap(utilon_icon_path)
                    icon_label.setPixmap(pixmap)
                else:
                    icon_label.setText("⭐")
                    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                if os.path.exists(error_icon_path):
                    pixmap = QPixmap(error_icon_path)
                    icon_label.setPixmap(pixmap)
                else:
                    icon_label.setText("❌")
                    icon_label.setStyleSheet("font-size: 45px;")
                    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if current_row_layout:
                current_row_layout.addWidget(icon_label)

        # Bonus row
        if getattr(self, '_accuracy_bonus_utilons', 0) > 0:
            reward_color = result_cfg.get('reward_color', '#E67E22')
            reward_font_px = int(self.config.get('fonts', {}).get('result_size', 32))
            
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 10, 0, 0)
            row_layout.setSpacing(12)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            accuracy_text = str(result_cfg.get('accuracy_reward_text', 'Bonus: 100% riktig'))
            label = QLabel(accuracy_text)
            label.setFont(create_font_px(FONT_NAME, reward_font_px, QFont.Weight.Bold))
            label.setStyleSheet(f"color: {reward_color};")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(label)

            for _ in range(min(int(self._accuracy_bonus_utilons), 10)):
                bonus_icon = QLabel()
                bonus_icon.setFixedSize(icon_size, icon_size)
                bonus_icon.setScaledContents(True)
                if os.path.exists(utilon_icon_path):
                    bonus_icon.setPixmap(QPixmap(utilon_icon_path))
                else:
                    bonus_icon.setText("⭐")
                    bonus_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row_layout.addWidget(bonus_icon)

            rows_layout.addWidget(row)
        
        self.icons_layout.addWidget(rows_container)
        
        self.icons_container.show()
        self._toggle_intro_cta(show_saveclose=True)
        self._intro_mode = "results"
        
        self.game_widget.hide()
        self.intro_widget.show()
        self.show_intro_buttons()
        
        if self.status_bar:
            self.status_bar.show()
        
        self._update_statusbar_utilons(force_reload=True)
    
    def save_stats(self, score: int, total: int, session_seconds: int = 0):
        """Save session stats (skip in dev_mode)"""
        if getattr(self, 'dev_mode', False):
            from core.dev_log import dev_log
            dev_log("LogikkQuiz", "save_stats", "skipped in dev_mode")
            return
        try:
            stats = stats_utils.load_stats()
            module_stats = stats_utils.ensure_module_entry(stats, 'logikkquiz', LOGIKKQUIZ_STATS_TEMPLATE)
            module_stats["total_sessions"] += 1
            module_stats["total_questions"] += total
            module_stats["correct_answers"] += score
            module_stats["last_played"] = format_compact_timestamp()

            best_prev = int(module_stats.get('best_session_seconds') or 0)
            if session_seconds and session_seconds > 0:
                if best_prev <= 0 or session_seconds < best_prev:
                    module_stats['best_session_seconds'] = int(session_seconds)

            # Daily stats
            from core.analytics import get_analytics
            analytics = get_analytics()
            today = datetime.now().strftime("%Y-%m-%d")
            daily = stats.setdefault("daily", {})
            day_data = daily.setdefault(today, {})
            sessions_list = day_data.setdefault("logikkquiz", [])
            
            weaks = []
            for i, q in enumerate(self.questions):
                if i < len(self.results) and self.results[i] is False:
                    weaks.append(q.get("type", "unknown"))
            
            sessions_list.append({
                "total_questions": total,
                "correct_answers": score,
                "session_seconds": session_seconds,
                "weaks": weaks,
                "timestamp": format_compact_timestamp()
            })

            stats_utils.save_stats(stats)
        except Exception as e:
            print(f"[LogikkQuiz] Error saving stats: {e}")


# Standalone run for testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogikkQuizApp()
    window.showFullScreen()
    sys.exit(app.exec())
