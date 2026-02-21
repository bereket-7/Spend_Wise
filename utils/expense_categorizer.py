import re
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from database.database_connection import get_connection, release_connection

logger = logging.getLogger(__name__)

class ExpenseCategorizer:
    """AI-powered expense categorization using NLP and machine learning"""
    
    def __init__(self):
        # Predefined category keywords and patterns
        self.category_patterns = {
            'Food': {
                'keywords': ['restaurant', 'food', 'grocery', 'coffee', 'lunch', 'dinner', 'breakfast', 
                           'pizza', 'burger', 'mcdonald', 'starbucks', 'subway', 'kfc',
                           'walmart', 'target', 'costco', 'whole foods', 'trader joe'],
                'merchants': ['mcdonalds', 'starbucks', 'subway', 'kfc', 'burger king', 'wendys'],
                'amount_ranges': [(5, 50)],  # Typical food transaction amounts
                'weight': 0.3
            },
            'Transportation': {
                'keywords': ['gas', 'uber', 'lyft', 'taxi', 'metro', 'bus', 'train', 'parking',
                           'car', 'auto', 'oil', 'tire', 'repair', 'toll', 'transit'],
                'merchants': ['uber', 'lyft', 'exxon', 'shell', 'bp', 'chevron', 'parking'],
                'amount_ranges': [(10, 100), (2, 20)],  # Gas and parking
                'weight': 0.25
            },
            'Shopping': {
                'keywords': ['amazon', 'walmart', 'target', 'best buy', 'costco', 'mall', 'clothing',
                           'shoes', 'electronics', 'furniture', 'home', 'decor', 'makeup'],
                'merchants': ['amazon', 'walmart', 'target', 'bestbuy', 'costco', 'nike', 'adidas'],
                'amount_ranges': [(20, 200)],
                'weight': 0.2
            },
            'Entertainment': {
                'keywords': ['movie', 'netflix', 'spotify', 'gaming', 'concert', 'theater', 'sports',
                           'subscription', 'streaming', 'youtube', 'disney', 'hulu'],
                'merchants': ['netflix', 'spotify', 'steam', 'playstation', 'xbox', 'disney+', 'hulu'],
                'amount_ranges': [(10, 30), (5, 15)],  # Subscriptions and tickets
                'weight': 0.15
            },
            'Bills': {
                'keywords': ['rent', 'mortgage', 'electric', 'water', 'gas', 'internet', 'phone',
                           'insurance', 'utility', 'cable', 'subscription', 'bill'],
                'merchants': ['comcast', 'verizon', 'at&t', 'geico', 'progressive'],
                'amount_ranges': [(50, 2000)],  # Typical bill amounts
                'weight': 0.25
            },
            'Healthcare': {
                'keywords': ['doctor', 'hospital', 'pharmacy', 'medicine', 'dental', 'vision',
                           'insurance', 'clinic', 'medical', 'health', 'prescription'],
                'merchants': ['cvs', 'walgreens', 'rite aid', 'hospital', 'clinic'],
                'amount_ranges': [(10, 500)],
                'weight': 0.2
            },
            'Education': {
                'keywords': ['tuition', 'course', 'book', 'school', 'college', 'university',
                           'learning', 'udemy', 'coursera', 'skillshare'],
                'merchants': ['udemy', 'coursera', 'skillshare', 'university'],
                'amount_ranges': [(20, 500)],
                'weight': 0.15
            },
            'Other': {
                'keywords': [],
                'merchants': [],
                'amount_ranges': [],
                'weight': 0.1
            }
        }
        
        # User-specific learning data
        self.user_preferences = {}
        self.user_corrections = defaultdict(list)
    
    def categorize_expense(self, description: str, amount: float, merchant: str = None, user_id: int = None) -> Dict[str, any]:
        """
        Categorize expense using multiple signals:
        - Description text analysis
        - Merchant name matching
        - Amount pattern recognition
        - User learning from corrections
        """
        try:
            # Clean and normalize inputs
            clean_description = self._clean_text(description)
            clean_merchant = self._clean_text(merchant) if merchant else ""
            
            # Get user-specific patterns if available
            user_patterns = self._get_user_patterns(user_id)
            
            # Calculate scores for each category
            category_scores = {}
            
            for category, patterns in self.category_patterns.items():
                score = 0
                
                # Text matching (40% weight)
                text_score = self._calculate_text_score(clean_description, patterns['keywords'])
                score += text_score * 0.4
                
                # Merchant matching (30% weight)
                merchant_score = self._calculate_merchant_score(clean_merchant, patterns['merchants'])
                score += merchant_score * 0.3
                
                # Amount pattern matching (20% weight)
                amount_score = self._calculate_amount_score(amount, patterns['amount_ranges'])
                score += amount_score * 0.2
                
                # User learning (10% weight)
                learning_score = self._calculate_learning_score(category, user_patterns)
                score += learning_score * 0.1
                
                category_scores[category] = score
            
            # Find best category
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category]
            
            # Apply confidence threshold
            if confidence < 0.3:
                best_category = 'Other'
                confidence = 0.5
            
            return {
                'category': best_category,
                'confidence': round(confidence, 2),
                'all_scores': {k: round(v, 2) for k, v in category_scores.items()},
                'reasoning': self._generate_reasoning(clean_description, clean_merchant, amount, best_category),
                'needs_confirmation': confidence < 0.6
            }
            
        except Exception as e:
            logger.error(f"Error categorizing expense: {e}")
            return {
                'category': 'Other',
                'confidence': 0.5,
                'error': 'Categorization failed'
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase and remove special characters
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _calculate_text_score(self, description: str, keywords: List[str]) -> float:
        """Calculate text matching score"""
        if not description or not keywords:
            return 0
        
        description_words = set(description.split())
        keyword_set = set(keywords)
        
        # Exact matches
        exact_matches = len(description_words & keyword_set)
        
        # Partial matches
        partial_matches = 0
        for word in description_words:
            for keyword in keywords:
                if keyword in word or word in keyword:
                    partial_matches += 1
                    break
        
        # Calculate score based on match ratio
        total_keywords = len(keyword_set)
        if total_keywords == 0:
            return 0
        
        match_ratio = (exact_matches * 2 + partial_matches) / (total_keywords * 2)
        return min(1.0, match_ratio)
    
    def _calculate_merchant_score(self, merchant: str, merchants: List[str]) -> float:
        """Calculate merchant matching score"""
        if not merchant or not merchants:
            return 0
        
        merchant_lower = merchant.lower()
        
        # Exact merchant match
        for known_merchant in merchants:
            if known_merchant.lower() in merchant_lower or merchant_lower in known_merchant.lower():
                return 1.0
        
        # Partial merchant match
        for known_merchant in merchants:
            if (known_merchant.lower() in merchant_lower or 
                any(word in merchant_lower for word in known_merchant.lower().split())):
                return 0.7
        
        return 0.0
    
    def _calculate_amount_score(self, amount: float, amount_ranges: List[Tuple[float, float]]) -> float:
        """Calculate amount pattern matching score"""
        if not amount_ranges:
            return 0.5  # Neutral score if no patterns
        
        for min_amount, max_amount in amount_ranges:
            if min_amount <= amount <= max_amount:
                return 1.0
        
        # Check if amount is close to any range
        min_distance = min(abs(amount - min_amount) for min_amount, max_amount in amount_ranges)
        if min_distance <= amount * 0.2:  # Within 20% of range
            return 0.8
        
        return 0.3
    
    def _calculate_learning_score(self, category: str, user_patterns: Dict) -> float:
        """Calculate user learning score"""
        if not user_patterns or category not in user_patterns:
            return 0.5  # Neutral score
        
        user_category_data = user_patterns[category]
        
        # Factor in frequency and accuracy
        frequency = user_category_data.get('frequency', 0)
        accuracy = user_category_data.get('accuracy', 0.5)
        
        # Higher frequency and accuracy = higher score
        return min(1.0, (frequency / 10) * accuracy)
    
    def _get_user_patterns(self, user_id: int) -> Dict:
        """Get learned patterns for a specific user"""
        if not user_id:
            return {}
        
        # In a real implementation, this would query a user_learning table
        # For now, return mock data
        return self.user_preferences.get(user_id, {})
    
    def _generate_reasoning(self, description: str, merchant: str, amount: float, category: str) -> str:
        """Generate human-readable reasoning for categorization"""
        reasons = []
        
        # Text-based reasoning
        category_keywords = self.category_patterns[category]['keywords']
        matched_keywords = [kw for kw in category_keywords if kw in description.lower()]
        if matched_keywords:
            reasons.append(f"Text contains: {', '.join(matched_keywords[:3])}")
        
        # Merchant-based reasoning
        if merchant:
            category_merchants = self.category_patterns[category]['merchants']
            matched_merchants = [m for m in category_merchants if m.lower() in merchant.lower()]
            if matched_merchants:
                reasons.append(f"Merchant: {matched_merchants[0]}")
        
        # Amount-based reasoning
        category_ranges = self.category_patterns[category]['amount_ranges']
        for min_amt, max_amt in category_ranges:
            if min_amt <= amount <= max_amt:
                reasons.append(f"Amount ${amount:.2f} matches typical range")
                break
        
        return " | ".join(reasons) if reasons else "Based on pattern matching"
    
    def learn_from_correction(self, user_id: int, original_description: str, 
                           original_category: str, correct_category: str, 
                           amount: float, merchant: str = None):
        """Learn from user corrections to improve future categorization"""
        try:
            # Update user-specific patterns
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = defaultdict(lambda: {'frequency': 0, 'accuracy': 0.5})
            
            user_data = self.user_preferences[user_id]
            
            # Update frequency for correct category
            user_data[correct_category]['frequency'] += 1
            
            # Update accuracy (simplified - would be more sophisticated in production)
            if original_category != correct_category:
                # Decrease confidence in original pattern
                user_data[original_category]['accuracy'] *= 0.9
                # Increase confidence in correct pattern
                user_data[correct_category]['accuracy'] = min(1.0, user_data[correct_category]['accuracy'] * 1.1)
            
            # Store correction for analysis
            self.user_corrections[user_id].append({
                'original_description': original_description,
                'original_category': original_category,
                'correct_category': correct_category,
                'amount': amount,
                'merchant': merchant,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Learned from user correction: {original_category} -> {correct_category}")
            
            # In production, this would save to database
            self._save_learning_to_database(user_id, original_description, correct_category, amount, merchant)
            
        except Exception as e:
            logger.error(f"Error learning from correction: {e}")
    
    def _save_learning_to_database(self, user_id: int, description: str, category: str, amount: float, merchant: str):
        """Save learning data to database (placeholder for implementation)"""
        # In a real implementation, this would save to a user_learning table
        # For now, just log the learning event
        logger.info(f"Saving learning data for user {user_id}: {description} -> {category}")
    
    def get_category_suggestions(self, partial_text: str, user_id: int = None) -> List[Dict]:
        """Get category suggestions based on partial input"""
        try:
            clean_partial = self._clean_text(partial_text)
            suggestions = []
            
            for category, patterns in self.category_patterns.items():
                score = self._calculate_text_score(clean_partial, patterns['keywords'])
                if score > 0.1:  # Only suggest relevant categories
                    suggestions.append({
                        'category': category,
                        'relevance': round(score, 2),
                        'sample_keywords': patterns['keywords'][:5]
                    })
            
            # Sort by relevance
            suggestions.sort(key=lambda x: x['relevance'], reverse=True)
            return suggestions[:5]  # Top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting category suggestions: {e}")
            return []
    
    def analyze_user_patterns(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze user's spending patterns and provide insights"""
        try:
            connection = get_connection()
            if not connection:
                return {}
            
            cursor = connection.cursor(dictionary=True)
            
            # Get recent expenses with categories
            start_date = datetime.now() - timedelta(days=days)
            query = """
            SELECT category, COUNT(*) as count, SUM(amount) as total, AVG(amount) as avg_amount
            FROM expense 
            WHERE user_id = %s AND date >= %s
            GROUP BY category
            ORDER BY total DESC
            """
            cursor.execute(query, (user_id, start_date.date()))
            results = cursor.fetchall()
            
            cursor.close()
            release_connection(connection)
            
            if not results:
                return {'message': 'No spending data available'}
            
            # Analyze patterns
            total_spending = sum(row['total'] for row in results)
            most_spent_category = results[0]['category'] if results else None
            most_frequent_category = max(results, key=lambda x: x['count'])['category'] if results else None
            
            # Generate insights
            insights = {
                'total_categories': len(results),
                'total_spending': total_spending,
                'category_breakdown': results,
                'most_spent_category': most_spent_category,
                'most_frequent_category': most_frequent_category,
                'average_transaction_size': total_spending / sum(row['count'] for row in results) if results else 0,
                'insights': self._generate_spending_insights(results)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing user patterns: {e}")
            return {'error': 'Unable to analyze patterns'}
    
    def _generate_spending_insights(self, category_data: List[Dict]) -> List[str]:
        """Generate insights from category spending data"""
        insights = []
        
        if not category_data:
            return insights
        
        # Find top spending category
        top_category = max(category_data, key=lambda x: x['total'])
        top_percentage = (top_category['total'] / sum(row['total'] for row in category_data)) * 100
        
        if top_percentage > 40:
            insights.append(f"{top_category['category']} accounts for {top_percentage:.1f}% of your spending")
        
        # Find frequent small transactions
        small_transactions = [row for row in category_data if row['avg_amount'] < 20]
        if len(small_transactions) > 3:
            insights.append(f"You have many small transactions - consider bundling purchases")
        
        # Check for unusual patterns
        for row in category_data:
            if row['count'] == 1 and row['total'] > 200:
                insights.append(f"Large one-time expense in {row['category']}: ${row['total']:.2f}")
        
        return insights
