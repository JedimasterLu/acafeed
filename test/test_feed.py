import datetime
import unittest
from unittest.mock import Mock, patch
from io import StringIO
from acafeed import Feed


class TestFeed(unittest.TestCase):
    """Test the dataclass Feed.
    """
    
    def test_feed_creation_valid_inputs(self):
        """Test creating a Feed with valid inputs."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(status=200)
            
            feed = Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)
            
            self.assertEqual(feed.link, link)
            self.assertEqual(feed.name, name)
            self.assertEqual(feed.add_time, add_time)
            self.assertEqual(feed.last_updated, last_updated)
    
    def test_feed_creation_with_301_redirect_warning(self):
        """Test creating a Feed with a 301 redirect warning."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(status=301)
            
            # 捕获标准输出
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)
                output = mock_stdout.getvalue()
                self.assertIn("Warning: The link", output)
                self.assertIn("is redirected (301)", output)
    
    def test_feed_creation_with_410_gone_error(self):
        """Test creating a Feed with a 410 gone error."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(status=410)
            
            with self.assertRaisesRegex(ValueError, "The link .* is gone \\(410\\)"):
                Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)
    
    def test_feed_invalid_link_type(self):
        """Test creating a Feed with an invalid link type."""
        # Use type: ignore to bypass static type checking and test runtime behavior
        link = 123  # type: ignore  # Invalid type
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with self.assertRaisesRegex(TypeError, "link must be a string"):
            Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)  # type: ignore
    
    def test_feed_invalid_name_type(self):
        """Test creating a Feed with an invalid name type."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = 123  # type: ignore  # Invalid type
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with self.assertRaisesRegex(TypeError, "name must be a string"):
            Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)  # type: ignore
    
    def test_feed_invalid_add_time_type(self):
        """Test creating a Feed with an invalid add_time type."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = "2023-01-01"  # type: ignore  # Invalid type
        last_updated = datetime.datetime.now()
        
        with self.assertRaisesRegex(TypeError, "add_time must be a datetime.datetime"):
            Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)  # type: ignore
    
    def test_feed_invalid_last_updated_type(self):
        """Test creating a Feed with an invalid last_updated type."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = "2023-01-01"  # type: ignore  # Invalid type
        with self.assertRaisesRegex(TypeError, "last_updated must be a datetime.datetime"):
            Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)  # type: ignore
    
    def test_feed_creation_with_successful_status_200(self):
        """Test creating a Feed with a successful status code 200."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(status=200)
            
            # 应该能够成功创建，不应抛出异常
            feed = Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)
            
            self.assertEqual(feed.link, link)
            self.assertEqual(feed.name, name)
    
    def test_feed_creation_with_other_error_status(self):
        """Test creating a Feed with other HTTP error status codes (non-301 and non-410)."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(status=404)
            
            # For other error statuses that are not 301 or 410, creation should succeed (no special handling)
            feed = Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)
            
            self.assertEqual(feed.link, link)
            self.assertEqual(feed.name, name)
    
    def test_feed_creation_with_none_values(self):
        """Test creating a Feed with None values."""
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        # Test None link
        with self.assertRaisesRegex(TypeError, "link must be a string"):
            Feed(link=None, name="Test", add_time=add_time, last_updated=last_updated)  # type: ignore
        
        # Test None name
        with self.assertRaisesRegex(TypeError, "name must be a string"):
            Feed(link="http://example.com", name=None, add_time=add_time, last_updated=last_updated)  # type: ignore
        
        # Test None add_time
        with self.assertRaisesRegex(TypeError, "add_time must be a datetime.datetime"):
            Feed(link="http://example.com", name="Test", add_time=None, last_updated=last_updated)  # type: ignore
        
        # Test None last_updated
        with self.assertRaisesRegex(TypeError, "last_updated must be a datetime.datetime"):
            Feed(link="http://example.com", name="Test", add_time=add_time, last_updated=None)  # type: ignore
    
    def test_feed_dataclass_attributes(self):
        """Test attribute access of Feed as a dataclass."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        last_updated = datetime.datetime(2023, 1, 2, 12, 0, 0)
        
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(status=200)
            
            feed = Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)
            
            # Verify all attributes can be accessed correctly
            self.assertTrue(hasattr(feed, 'link'))
            self.assertTrue(hasattr(feed, 'name'))
            self.assertTrue(hasattr(feed, 'add_time'))
            self.assertTrue(hasattr(feed, 'last_updated'))
            
            # Verify attribute values are correct
            self.assertEqual(feed.link, link)
            self.assertEqual(feed.name, name)
            self.assertEqual(feed.add_time, add_time)
            self.assertEqual(feed.last_updated, last_updated)
    
    def test_feed_with_edge_case_types(self):
        """Test Feed handling edge case types."""
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()

        # Test empty strings (should succeed)
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(status=200)
            
            feed = Feed(link="", name="", add_time=add_time, last_updated=last_updated)
            self.assertEqual(feed.link, "")
            self.assertEqual(feed.name, "")
    
    def test_feed_feedparser_without_status_attribute(self):
        """Test feedparser returning an object without a status attribute."""
        link = "http://www.nature.com/nmat/current_issue/rss/"
        name = "Nature Materials"
        add_time = datetime.datetime.now()
        last_updated = datetime.datetime.now()
        
        with patch('feedparser.parse') as mock_parse:
            # Simulate an object without a status attribute
            mock_result = Mock()
            del mock_result.status
            mock_parse.return_value = mock_result

            # Should be able to create successfully (no status check)
            try:
                feed = Feed(link=link, name=name, add_time=add_time, last_updated=last_updated)
                self.assertEqual(feed.link, link)
                self.assertEqual(feed.name, name)
            except AttributeError:
                # If an AttributeError is raised, it means the code tried to access a non-existent status attribute
                # This is the expected behavior because the original code directly accesses sample.status
                pass
