import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from database.database_connection import get_connection, release_connection
from database.expense_query import get_all_expenses

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Detects and manages recurring subscriptions and charges"""
    
    def __init__(self):
        # Common subscription patterns and merchants
        self.subscription_patterns = {
            # Streaming services
            'netflix': {
                'keywords': ['netflix'],
                'merchants': ['netflix.com', 'netflix'],
                'typical_amounts': [8.99, 9.99, 15.99, 17.99, 19.99],
                'frequency': 'monthly',
                'category': 'Entertainment'
            },
            'spotify': {
                'keywords': ['spotify'],
                'merchants': ['spotify.com', 'spotify'],
                'typical_amounts': [9.99, 10.99, 14.99],
                'frequency': 'monthly',
                'category': 'Entertainment'
            },
            'disney_plus': {
                'keywords': ['disney+', 'disney plus'],
                'merchants': ['disneyplus.com', 'disney.com'],
                'typical_amounts': [7.99, 13.99],
                'frequency': 'monthly',
                'category': 'Entertainment'
            },
            'hulu': {
                'keywords': ['hulu'],
                'merchants': ['hulu.com', 'hulu'],
                'typical_amounts': [5.99, 6.99, 11.99, 69.99],
                'frequency': 'monthly',
                'category': 'Entertainment'
            },
            
            # Software & Apps
            'adobe': {
                'keywords': ['adobe', 'creative cloud'],
                'merchants': ['adobe.com', 'adobe'],
                'typical_amounts': [9.99, 19.99, 29.99],
                'frequency': 'monthly',
                'category': 'Software'
            },
            'microsoft': {
                'keywords': ['microsoft', 'office 365', 'azure'],
                'merchants': ['microsoft.com', 'microsoft'],
                'typical_amounts': [9.99, 12.99, 19.99, 99.99],
                'frequency': 'monthly',
                'category': 'Software'
            },
            'apple': {
                'keywords': ['icloud', 'apple music', 'apple tv+'],
                'merchants': ['apple.com', 'itunes'],
                'typical_amounts': [2.99, 4.99, 9.99, 14.99],
                'frequency': 'monthly',
                'category': 'Software'
            },
            
            # Communication
            'phone_bill': {
                'keywords': ['verizon', 'at&t', 't-mobile', 'sprint', 'phone bill'],
                'merchants': ['verizon.com', 'att.com', 't-mobile.com'],
                'typical_amounts': [30, 50, 80, 100, 150],
                'frequency': 'monthly',
                'category': 'Bills'
            },
            'internet': {
                'keywords': ['comcast', 'xfinity', 'spectrum', 'cox', 'internet'],
                'merchants': ['comcast.com', 'xfinity.com', 'spectrum.com'],
                'typical_amounts': [30, 50, 70, 100],
                'frequency': 'monthly',
                'category': 'Bills'
            },
            
            # Fitness & Wellness
            'gym': {
                'keywords': ['gym', 'fitness', 'planet fitness', 'la fitness'],
                'merchants': ['planetfitness.com', '24hourfitness.com'],
                'typical_amounts': [10, 20, 30, 50, 100],
                'frequency': 'monthly',
                'category': 'Healthcare'
            },
            
            # Shopping & Services
            'amazon_prime': {
                'keywords': ['amazon prime', 'prime'],
                'merchants': ['amazon.com', 'amazon'],
                'typical_amounts': [12.99, 14.99, 119.00],
                'frequency': 'monthly' if 12.99 in [12.99, 14.99] else 'yearly',
                'category': 'Shopping'
            },
            'costco': {
                'keywords': ['costco'],
                'merchants': ['costco.com', 'costco'],
                'typical_amounts': [60, 120],
                'frequency': 'yearly',
                'category': 'Shopping'
            }
        }
        
        # Detection thresholds
        self.min_occurrences = 3  # Minimum occurrences to consider as subscription
        self.amount_variance_threshold = 0.15  # 15% variance allowed
        self.day_variance_threshold = 5  # 5 days variance allowed
    
    def detect_subscriptions(self, user_id: int, days: int = 90) -> Dict[str, any]:
        """Detect subscriptions from user's expense history"""
        try:
            connection = get_connection()
            if not connection:
                return {'error': 'Database connection failed'}
            
            cursor = connection.cursor(dictionary=True)
            
            # Get expenses for analysis period
            start_date = datetime.now() - timedelta(days=days)
            query = """
            SELECT description, amount, date, category
            FROM expense 
            WHERE user_id = %s AND date >= %s
            ORDER BY date DESC
            """
            cursor.execute(query, (user_id, start_date.date()))
            expenses = cursor.fetchall()
            
            cursor.close()
            release_connection(connection)
            
            if not expenses:
                return {'message': 'No expense data available for analysis'}
            
            # Group similar expenses
            potential_subscriptions = self._find_recurring_expenses(expenses)
            
            # Analyze and categorize subscriptions
            detected_subscriptions = []
            total_monthly_cost = 0
            
            for subscription_group in potential_subscriptions:
                subscription_info = self._analyze_subscription_group(subscription_group, user_id)
                if subscription_info:
                    detected_subscriptions.append(subscription_info)
                    if subscription_info['frequency'] == 'monthly':
                        total_monthly_cost += subscription_info['monthly_cost']
                    elif subscription_info['frequency'] == 'yearly':
                        total_monthly_cost += subscription_info['monthly_cost']
            
            # Generate insights and recommendations
            insights = self._generate_subscription_insights(detected_subscriptions, total_monthly_cost)
            
            return {
                'subscriptions': detected_subscriptions,
                'total_monthly_cost': round(total_monthly_cost, 2),
                'total_annual_cost': round(total_monthly_cost * 12, 2),
                'insights': insights,
                'analysis_period': f"{days} days",
                'detected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting subscriptions: {e}")
            return {'error': 'Subscription detection failed'}
    
    def _find_recurring_expenses(self, expenses: List[Dict]) -> List[List[Dict]]:
        """Find groups of similar recurring expenses"""
        # Normalize expense descriptions for matching
        normalized_expenses = []
        for expense in expenses:
            normalized = self._normalize_description(expense['description'])
            normalized_expenses.append({
                **expense,
                'normalized_description': normalized,
                'month_day': datetime.strptime(expense['date'], '%Y-%m-%d').day
            })
        
        # Group by normalized description
        expense_groups = defaultdict(list)
        for expense in normalized_expenses:
            key = expense['normalized_description']
            expense_groups[key].append(expense)
        
        # Filter for potential subscriptions
        potential_subscriptions = []
        for description, group in expense_groups.items():
            if self._is_subscription_candidate(group):
                potential_subscriptions.append(group)
        
        return potential_subscriptions
    
    def _normalize_description(self, description: str) -> str:
        """Normalize expense description for better matching"""
        if not description:
            return ""
        
        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^\w\s]', ' ', description.lower())
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['payment to', 'charge from', 'debit from', 'credit to']
        for prefix in prefixes_to_remove:
            normalized = normalized.replace(prefix, '')
        
        # Remove extra spaces and common words
        words_to_remove = ['payment', 'charge', 'debit', 'credit', 'auto', 'recurring']
        words = normalized.split()
        words = [word for word in words if word not in words_to_remove and len(word) > 2]
        
        return ' '.join(words).strip()
    
    def _is_subscription_candidate(self, expense_group: List[Dict]) -> bool:
        """Determine if a group of expenses is likely a subscription"""
        if len(expense_group) < self.min_occurrences:
            return False
        
        # Check amount consistency
        amounts = [expense['amount'] for expense in expense_group]
        avg_amount = sum(amounts) / len(amounts)
        amount_variance = sum((amt - avg_amount) ** 2 for amt in amounts) / len(amounts)
        amount_std_dev = amount_variance ** 0.5
        
        # Allow some variance but not too much
        if avg_amount > 0 and (amount_std_dev / avg_amount) > self.amount_variance_threshold:
            return False
        
        # Check timing consistency (monthly pattern)
        if self._has_monthly_pattern(expense_group):
            return True
        
        # Check if it matches known subscription patterns
        sample_description = expense_group[0]['normalized_description']
        for service_name, pattern in self.subscription_patterns.items():
            if (service_name in sample_description or 
                any(keyword in sample_description for keyword in pattern['keywords'])):
                return True
        
        return False
    
    def _has_monthly_pattern(self, expense_group: List[Dict]) -> bool:
        """Check if expenses follow a monthly pattern"""
        if len(expense_group) < 3:
            return False
        
        # Group by day of month
        day_groups = defaultdict(list)
        for expense in expense_group:
            day_groups[expense['month_day']].append(expense)
        
        # Check if most expenses occur on similar days
        common_days = [day for day, expenses in day_groups.items() if len(expenses) >= 2]
        
        return len(common_days) >= 2  # At least 2 common days suggest monthly pattern
    
    def _analyze_subscription_group(self, expense_group: List[Dict], user_id: int) -> Optional[Dict]:
        """Analyze a group of recurring expenses to determine subscription details"""
        if not expense_group:
            return None
        
        # Calculate subscription metrics
        amounts = [expense['amount'] for expense in expense_group]
        avg_amount = sum(amounts) / len(amounts)
        most_common_amount = max(set(amounts), key=amounts.count)
        
        # Determine frequency
        frequency = self._determine_frequency(expense_group)
        
        # Identify the service
        service_name = self._identify_service(expense_group[0])
        
        # Calculate monthly cost
        if frequency == 'monthly':
            monthly_cost = most_common_amount
        elif frequency == 'yearly':
            monthly_cost = most_common_amount / 12
        else:
            monthly_cost = avg_amount
        
        return {
            'service_name': service_name,
            'frequency': frequency,
            'monthly_cost': round(monthly_cost, 2),
            'annual_cost': round(monthly_cost * 12, 2),
            'occurrences': len(expense_group),
            'average_amount': round(avg_amount, 2),
            'most_common_amount': round(most_common_amount, 2),
            'category': self.subscription_patterns.get(service_name, {}).get('category', 'Other'),
            'confidence': self._calculate_confidence(expense_group, service_name),
            'recent_charges': sorted(expense_group, key=lambda x: x['date'], reverse=True)[:3],
            'first_charge': min(expense_group, key=lambda x: x['date'])['date'],
            'last_charge': max(expense_group, key=lambda x: x['date'])['date']
        }
    
    def _determine_frequency(self, expense_group: List[Dict]) -> str:
        """Determine the frequency of recurring charges"""
        if len(expense_group) < 3:
            return 'unknown'
        
        # Analyze time between charges
        dates = [datetime.strptime(expense['date'], '%Y-%m-%d') for expense in expense_group]
        dates.sort()
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)
        
        if not intervals:
            return 'unknown'
        
        avg_interval = sum(intervals) / len(intervals)
        
        # Determine frequency based on average interval
        if 25 <= avg_interval <= 35:  # Monthly (30 days ± 5)
            return 'monthly'
        elif 85 <= avg_interval <= 95:  # Quarterly (90 days ± 5)
            return 'quarterly'
        elif 350 <= avg_interval <= 380:  # Yearly (365 days ± 15)
            return 'yearly'
        else:
            return 'irregular'
    
    def _identify_service(self, expense: Dict) -> str:
        """Identify the subscription service from expense description"""
        description = expense.get('normalized_description', expense['description']).lower()
        amount = expense['amount']
        
        # Check against known patterns
        best_match = None
        best_score = 0
        
        for service_name, pattern in self.subscription_patterns.items():
            score = 0
            
            # Keyword matching
            for keyword in pattern['keywords']:
                if keyword in description:
                    score += 2
            
            # Amount matching
            for typical_amount in pattern['typical_amounts']:
                if abs(amount - typical_amount) <= typical_amount * 0.1:  # Within 10%
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = service_name
        
        return best_match if best_match else 'unknown'
    
    def _calculate_confidence(self, expense_group: List[Dict], service_name: str) -> float:
        """Calculate confidence score for subscription detection"""
        if service_name == 'unknown':
            return 0.3  # Low confidence for unknown services
        
        base_confidence = 0.5
        
        # Increase confidence based on occurrences
        occurrences = len(expense_group)
        if occurrences >= 6:
            base_confidence += 0.3
        elif occurrences >= 4:
            base_confidence += 0.2
        elif occurrences >= 3:
            base_confidence += 0.1
        
        # Increase confidence if it's a known service
        if service_name in self.subscription_patterns:
            base_confidence += 0.2
        
        return min(1.0, base_confidence)
    
    def _generate_subscription_insights(self, subscriptions: List[Dict], total_monthly_cost: float) -> List[Dict]:
        """Generate insights and recommendations about subscriptions"""
        insights = []
        
        if not subscriptions:
            return insights
        
        # Cost analysis
        if total_monthly_cost > 200:
            insights.append({
                'type': 'cost_warning',
                'priority': 'high',
                'title': 'High Subscription Costs',
                'description': f'You spend ${total_monthly_cost:.2f}/month on subscriptions',
                'recommendation': 'Review and cancel unused subscriptions'
            })
        
        # Find most expensive subscription
        most_expensive = max(subscriptions, key=lambda x: x['monthly_cost']) if subscriptions else None
        if most_expensive and most_expensive['monthly_cost'] > 50:
            insights.append({
                'type': 'expensive_subscription',
                'priority': 'medium',
                'title': 'Expensive Subscription Detected',
                'description': f"{most_expensive['service_name']} costs ${most_expensive['monthly_cost']:.2f}/month",
                'recommendation': 'Look for cheaper alternatives or cancel if unused'
            })
        
        # Check for unused subscriptions (based on recent activity)
        unused_subs = [sub for sub in subscriptions if sub['confidence'] < 0.6]
        if unused_subs:
            insights.append({
                'type': 'unused_subscriptions',
                'priority': 'medium',
                'title': 'Potentially Unused Subscriptions',
                'description': f'{len(unused_subs)} subscriptions may no longer be used',
                'recommendation': 'Review these subscriptions and cancel if unnecessary'
            })
        
        # Duplicate services
        service_categories = defaultdict(list)
        for sub in subscriptions:
            if sub['service_name'] != 'unknown':
                service_categories[sub['category']].append(sub)
        
        duplicate_categories = [cat for cat, subs in service_categories.items() if len(subs) > 1]
        if duplicate_categories:
            insights.append({
                'type': 'duplicate_services',
                'priority': 'low',
                'title': 'Duplicate Service Categories',
                'description': f'You have multiple services in: {", ".join(duplicate_categories)}',
                'recommendation': 'Consider consolidating or removing duplicates'
            })
        
        # Optimization opportunities
        streaming_subs = [sub for sub in subscriptions if sub['category'] == 'Entertainment']
        if len(streaming_subs) > 3:
            insights.append({
                'type': 'optimization',
                'priority': 'medium',
                'title': 'Streaming Service Optimization',
                'description': f'You have {len(streaming_subs)} streaming subscriptions',
                'recommendation': 'Consider rotating services or using family plans'
            })
        
        return insights
    
    def get_alternative_services(self, service_name: str, max_cost: float = None) -> List[Dict]:
        """Suggest alternative services with better pricing"""
        alternatives = {
            'streaming': [
                {'name': 'Disney+ Bundle', 'cost': 13.99, 'features': ['Disney+, Hulu, ESPN+']},
                {'name': 'Amazon Prime Video', 'cost': 8.99, 'features': ['Prime Video, Prime Shipping']},
                {'name': 'Paramount+', 'cost': 4.99, 'features': ['Movies, TV Shows']}
            ],
            'music': [
                {'name': 'YouTube Music', 'cost': 9.99, 'features': ['Ad-free music, YouTube Premium']},
                {'name': 'Apple Music', 'cost': 9.99, 'features': ['Lossless audio, Spatial audio']},
                {'name': 'Tidal', 'cost': 9.99, 'features': ['Hi-fi audio, Artist payouts']}
            ],
            'software': [
                {'name': 'Google Workspace', 'cost': 6.00, 'features': ['Docs, Sheets, Drive, Gmail']},
                {'name': 'LibreOffice', 'cost': 0.00, 'features': ['Free office suite']},
                {'name': 'OpenOffice', 'cost': 0.00, 'features': ['Free office suite']}
            ]
        }
        
        # Determine category and suggest alternatives
        if service_name in self.subscription_patterns:
            category = self.subscription_patterns[service_name]['category']
            
            # Map to alternative categories
            if category == 'Entertainment':
                return alternatives.get('streaming', [])
            elif category == 'Software':
                return alternatives.get('music', []) + alternatives.get('software', [])
        
        return []
    
    def track_subscription_changes(self, user_id: int, days: int = 30) -> Dict[str, any]:
        """Track subscription changes (new, canceled, price changes)"""
        try:
            # Get current subscriptions
            current_subs = self.detect_subscriptions(user_id, days)
            
            # Get historical data (would need subscription_history table)
            # For now, return mock analysis
            return {
                'new_subscriptions': [],  # Would compare with previous period
                'canceled_subscriptions': [],
                'price_changes': [],
                'analysis_period': f"{days} days",
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error tracking subscription changes: {e}")
            return {'error': 'Unable to track subscription changes'}
