"""History service for managing EEG data history"""

import json
from typing import List, Dict
from pathlib import Path
from models.eeg_models import EegHistoryModel, ConfigParams, EegFaultModel


class HistoryService:
    """Service for managing EEG history and pattern recognition"""

    def __init__(self):
        self.history: List[EegHistoryModel] = []

    def add(self, record: EegHistoryModel):
        """Add a record to history"""
        self.history.append(record)

    def clear(self):
        """Clear all history"""
        self.history.clear()

    def count(self) -> int:
        """Get history count"""
        return len(self.history)

    def load(self, path: str):
        """Load history from JSON file"""
        file_path = Path(path)
        if not file_path.exists():
            print(f"File not found: {path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = [EegHistoryModel.from_dict(item) for item in data]
                print(f"Loaded {len(self.history)} records from history")
        except Exception as e:
            print(f"Error loading history: {e}")

    def save(self, path: str):
        """Save history to JSON file"""
        if not self.history:
            print("No history to save")
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                data = [record.to_dict() for record in self.history]
                json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Saved {len(self.history)} records to {path}")
        except Exception as e:
            print(f"Error saving history: {e}")

    def get_event_name_by(self, current: EegHistoryModel, config: ConfigParams) -> str:
        """
        Get event name by matching current data with historical patterns
        """
        if not self.history:
            return ""

        results_list = []
        faults = list(reversed(config.eeg_faults))
        current_results = list(self.history)

        for i in range(config.multi_count):
            if i != 0:
                current_results = results_list[i - 1]

            if i < len(faults):
                results_list.append(
                    self._search_events(current_results, current, faults[i])
                )

        results_list.reverse()

        for results in results_list:
            if not results:
                continue

            # Count events
            counts = {
                'ml': sum(1 for x in results if x.event_name == 'ml'),
                'mr': sum(1 for x in results if x.event_name == 'mr'),
                'mu': sum(1 for x in results if x.event_name == 'mu'),
                'md': sum(1 for x in results if x.event_name == 'md'),
                'stop': sum(1 for x in results if x.event_name == 'stop')
            }

            print(f"ml: {counts['ml']}, mr: {counts['mr']}, "
                  f"mu: {counts['mu']}, md: {counts['md']}, stop: {counts['stop']}")

            # Return most common event
            if counts:
                max_event = max(counts.items(), key=lambda x: x[1])
                if max_event[1] > 0:
                    return max_event[0]

        return ""

    def _search_events(
        self,
        results: List[EegHistoryModel],
        current: EegHistoryModel,
        fault: EegFaultModel
    ) -> List[EegHistoryModel]:
        """Search for matching events within fault tolerance"""
        if not results or not fault:
            return results

        # Filter by attention
        if fault.attention != 0:
            results = [
                x for x in results
                if current.attention - fault.attention <= x.attention <= current.attention + fault.attention
            ]
        if not results:
            return results

        # Filter by meditation
        if fault.meditation != 0:
            results = [
                x for x in results
                if current.meditation - fault.meditation <= x.meditation <= current.meditation + fault.meditation
            ]
        if not results:
            return results

        # Filter by delta
        if fault.delta != 0:
            results = [
                x for x in results
                if current.delta - fault.delta <= x.delta <= current.delta + fault.delta
            ]
        if not results:
            return results

        # Filter by theta
        if fault.theta != 0:
            results = [
                x for x in results
                if current.theta - fault.theta <= x.theta <= current.theta + fault.theta
            ]
        if not results:
            return results

        # Filter by high beta
        if fault.high_beta != 0:
            results = [
                x for x in results
                if current.high_beta - fault.high_beta <= x.high_beta <= current.high_beta + fault.high_beta
            ]
        if not results:
            return results

        # Filter by low beta
        if fault.low_beta != 0:
            results = [
                x for x in results
                if current.low_beta - fault.low_beta <= x.low_beta <= current.low_beta + fault.low_beta
            ]
        if not results:
            return results

        # Filter by high alpha
        if fault.high_alpha != 0:
            results = [
                x for x in results
                if current.high_alpha - fault.high_alpha <= x.high_alpha <= current.high_alpha + fault.high_alpha
            ]
        if not results:
            return results

        # Filter by low alpha
        if fault.low_alpha != 0:
            results = [
                x for x in results
                if current.low_alpha - fault.low_alpha <= x.low_alpha <= current.low_alpha + fault.low_alpha
            ]
        if not results:
            return results

        # Filter by high gamma
        if fault.high_gamma != 0:
            results = [
                x for x in results
                if current.high_gamma - fault.high_gamma <= x.high_gamma <= current.high_gamma + fault.high_gamma
            ]
        if not results:
            return results

        # Filter by low gamma
        if fault.low_gamma != 0:
            results = [
                x for x in results
                if current.low_gamma - fault.low_gamma <= x.low_gamma <= current.low_gamma + fault.low_gamma
            ]

        return results
