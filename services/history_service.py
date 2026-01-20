"""History service for managing EEG data history"""

import json
import logging
from typing import List, Dict
from pathlib import Path
from models.eeg_models import EegHistoryModel, ConfigParams, EegFaultModel

logger = logging.getLogger(__name__)


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
            logger.warning(f"History file not found: {path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = [EegHistoryModel.from_dict(item) for item in data]
                logger.info(f"Loaded {len(self.history)} records from history")
        except Exception as e:
            logger.error(f"Error loading history: {e}", exc_info=True)

    def save(self, path: str):
        """Save history to JSON file"""
        if not self.history:
            logger.warning("No history to save")
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                data = [record.to_dict() for record in self.history]
                json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved {len(self.history)} records to {path}")
        except Exception as e:
            logger.error(f"Error saving history: {e}", exc_info=True)

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

            logger.debug(f"Event counts - ml: {counts['ml']}, mr: {counts['mr']}, "
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
        """
        Search for matching events within fault tolerance.
        
        Filters historical records that match the current EEG data
        within specified tolerance ranges for each parameter.
        
        Args:
            results: List of historical EEG records to filter
            current: Current EEG data to match against
            fault: Fault tolerance values for each parameter
            
        Returns:
            Filtered list of matching EEG records
        """
        if not results or not fault:
            return results

        # Define parameters to check (field_name, use_filter)
        # Order matters: filter most selective parameters first for better performance
        filter_params = [
            ('attention', fault.attention),
            ('meditation', fault.meditation),
            ('delta', fault.delta),
            ('theta', fault.theta),
            ('high_beta', fault.high_beta),
            ('low_beta', fault.low_beta),
            ('high_alpha', fault.high_alpha),
            ('low_alpha', fault.low_alpha),
            ('high_gamma', fault.high_gamma),
            ('low_gamma', fault.low_gamma),
        ]

        # Filter results using all active parameters in one pass
        def matches_criteria(record: EegHistoryModel) -> bool:
            """Check if record matches all fault tolerance criteria"""
            for field_name, tolerance in filter_params:
                if tolerance == 0:
                    continue  # Skip disabled parameters
                
                current_value = getattr(current, field_name)
                record_value = getattr(record, field_name)
                
                # Check if value is within tolerance range
                if not (current_value - tolerance <= record_value <= current_value + tolerance):
                    return False
            
            return True

        # Single-pass filtering
        return [record for record in results if matches_criteria(record)]
