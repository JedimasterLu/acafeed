import datetime
import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from io import StringIO
from acafeed import FeedSource


class TestFeedSource(unittest.TestCase):
    """Unit tests for the FeedSource class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.feed_source = FeedSource()
        self.test_link = "http://www.nature.com/nmat/current_issue/rss/"
        self.test_name = "Nature Materials"
        
    def test_init(self):
        """Test FeedSource initialization."""
        feed_source = FeedSource()
        self.assertEqual(feed_source._feeds, [])
        self.assertEqual(feed_source._feed_names, [])
    
    @patch('feedparser.parse')
    def test_add_new_feed_success(self, mock_parse):
        """Test successfully adding a new feed."""
        mock_parse.return_value = Mock(status=200)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.add(self.test_link, self.test_name)
            output = mock_stdout.getvalue()
            self.assertIn(f"The feed {self.test_name} has been added.", output)
        
        self.assertEqual(len(self.feed_source._feeds), 1)
        self.assertEqual(len(self.feed_source._feed_names), 1)
        self.assertIn(self.test_name, self.feed_source._feed_names)
        
        added_feed = self.feed_source._feeds[0]
        self.assertEqual(added_feed.link, self.test_link)
        self.assertEqual(added_feed.name, self.test_name)
        self.assertIsInstance(added_feed.add_time, datetime.datetime)
        self.assertIsInstance(added_feed.last_updated, datetime.datetime)
    
    @patch('feedparser.parse')
    def test_add_duplicate_name_feed(self, mock_parse):
        """Test adding a feed with duplicate name."""
        mock_parse.return_value = Mock(status=200)
        
        # Add first feed
        self.feed_source.add(self.test_link, self.test_name)
        
        # Try to add feed with same name
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.add("http://example.com/rss", self.test_name)
            output = mock_stdout.getvalue()
            self.assertIn(f"The feed name {self.test_name} is already in use.", output)
        
        # Should still have only one feed
        self.assertEqual(len(self.feed_source._feeds), 1)
        self.assertEqual(len(self.feed_source._feed_names), 1)
    
    @patch('feedparser.parse')
    def test_add_feed_with_410_error(self, mock_parse):
        """Test adding a feed that returns 410 error."""
        mock_parse.return_value = Mock(status=410)
        
        with self.assertRaisesRegex(ValueError, "The link .* is gone \\(410\\)"):
            self.feed_source.add(self.test_link, self.test_name)
        
        # Feed should not be added due to error
        self.assertEqual(len(self.feed_source._feeds), 0)
        self.assertEqual(len(self.feed_source._feed_names), 0)
    
    @patch('feedparser.parse')
    def test_remove_existing_feed(self, mock_parse):
        """Test removing an existing feed."""
        mock_parse.return_value = Mock(status=200)
        
        # Add a feed first
        self.feed_source.add(self.test_link, self.test_name)
        self.assertEqual(len(self.feed_source._feeds), 1)
        
        # Remove the feed
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.remove(self.test_name)
            output = mock_stdout.getvalue()
            self.assertIn(f"The feed {self.test_name} has been removed.", output)
        
        self.assertEqual(len(self.feed_source._feeds), 0)
        self.assertEqual(len(self.feed_source._feed_names), 0)
    
    def test_remove_nonexistent_feed(self):
        """Test removing a feed that doesn't exist."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.remove("Nonexistent Feed")
            output = mock_stdout.getvalue()
            self.assertIn("The feed Nonexistent Feed was not found in the list.", output)
    
    @patch('feedparser.parse')
    def test_change_feed_link_only(self, mock_parse):
        """Test changing only the link of an existing feed."""
        mock_parse.return_value = Mock(status=200)
        
        # Add a feed first
        self.feed_source.add(self.test_link, self.test_name)
        
        # Change only the link
        new_link = "http://example.com/new_rss"
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.change(self.test_name, new_link=new_link)
            output = mock_stdout.getvalue()
            self.assertIn(f"The feed {self.test_name} has been updated.", output)
        
        # Check that link was updated but name remained the same
        updated_feed = self.feed_source._feeds[0]
        self.assertEqual(updated_feed.link, new_link)
        self.assertEqual(updated_feed.name, self.test_name)
        self.assertIn(self.test_name, self.feed_source._feed_names)
    
    @patch('feedparser.parse')
    def test_change_feed_name_only(self, mock_parse):
        """Test changing only the name of an existing feed."""
        mock_parse.return_value = Mock(status=200)
        
        # Add a feed first
        self.feed_source.add(self.test_link, self.test_name)
        
        # Change only the name
        new_name = "New Nature Materials"
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.change(self.test_name, new_name=new_name)
            output = mock_stdout.getvalue()
            self.assertIn(f"The feed {self.test_name} has been updated.", output)
        
        # Check that name was updated but link remained the same
        updated_feed = self.feed_source._feeds[0]
        self.assertEqual(updated_feed.link, self.test_link)
        self.assertEqual(updated_feed.name, new_name)
        self.assertNotIn(self.test_name, self.feed_source._feed_names)
        self.assertIn(new_name, self.feed_source._feed_names)
    
    @patch('feedparser.parse')
    def test_change_feed_both_link_and_name(self, mock_parse):
        """Test changing both link and name of an existing feed."""
        mock_parse.return_value = Mock(status=200)
        
        # Add a feed first
        self.feed_source.add(self.test_link, self.test_name)
        
        # Change both link and name
        new_link = "http://example.com/new_rss"
        new_name = "New Nature Materials"
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.change(self.test_name, new_link=new_link, new_name=new_name)
            output = mock_stdout.getvalue()
            self.assertIn(f"The feed {self.test_name} has been updated.", output)
        
        # Check that both were updated
        updated_feed = self.feed_source._feeds[0]
        self.assertEqual(updated_feed.link, new_link)
        self.assertEqual(updated_feed.name, new_name)
        self.assertNotIn(self.test_name, self.feed_source._feed_names)
        self.assertIn(new_name, self.feed_source._feed_names)
    
    @patch('feedparser.parse')
    def test_change_feed_name_to_existing_name(self, mock_parse):
        """Test changing feed name to an already existing name."""
        mock_parse.return_value = Mock(status=200)
        
        # Add two feeds
        self.feed_source.add(self.test_link, self.test_name)
        second_name = "Second Feed"
        self.feed_source.add("http://example.com/rss", second_name)
        
        # Try to change second feed name to first feed's name
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.change(second_name, new_name=self.test_name)
            output = mock_stdout.getvalue()
            self.assertIn(f"The feed name {self.test_name} is already in use.", output)
        
        # Names should remain unchanged
        self.assertIn(self.test_name, self.feed_source._feed_names)
        self.assertIn(second_name, self.feed_source._feed_names)
    
    def test_change_no_parameters(self):
        """Test change method with no parameters specified."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.change("Some Feed")
            output = mock_stdout.getvalue()
            self.assertIn("No changes specified.", output)
    
    def test_change_nonexistent_feed(self):
        """Test changing a feed that doesn't exist."""
        # change method doesn't print anything for nonexistent feeds
        # it just returns without doing anything
        original_feeds_count = len(self.feed_source._feeds)
        self.feed_source.change("Nonexistent Feed", new_link="http://example.com")
        self.assertEqual(len(self.feed_source._feeds), original_feeds_count)
    
    @patch('feedparser.parse')
    def test_search_with_matches(self, mock_parse):
        """Test searching for feeds with keyword matches."""
        mock_parse.return_value = Mock(status=200)
        
        # Add multiple feeds
        self.feed_source.add(self.test_link, "Nature Materials")
        self.feed_source.add("http://example.com/rss", "Science Materials")
        self.feed_source.add("http://test.com/rss", "Physics Today")
        
        # Search for "materials"
        results = self.feed_source.search("materials")
        self.assertEqual(len(results), 2)
        
        # Check that correct feeds are returned
        result_names = [feed.name for feed in results]
        self.assertIn("Nature Materials", result_names)
        self.assertIn("Science Materials", result_names)
        self.assertNotIn("Physics Today", result_names)
    
    @patch('feedparser.parse')
    def test_search_case_insensitive(self, mock_parse):
        """Test that search is case insensitive."""
        mock_parse.return_value = Mock(status=200)
        
        self.feed_source.add(self.test_link, "Nature Materials")
        
        # Search with different cases
        results_lower = self.feed_source.search("nature")
        results_upper = self.feed_source.search("NATURE")
        results_mixed = self.feed_source.search("NaTuRe")
        
        self.assertEqual(len(results_lower), 1)
        self.assertEqual(len(results_upper), 1)
        self.assertEqual(len(results_mixed), 1)
        
        for results in [results_lower, results_upper, results_mixed]:
            self.assertEqual(results[0].name, "Nature Materials")
    
    def test_search_no_matches(self):
        """Test searching with no matches."""
        results = self.feed_source.search("nonexistent")
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])
    
    @patch('feedparser.parse')
    def test_pprint_all_feeds(self, mock_parse):
        """Test printing all feeds."""
        mock_parse.return_value = Mock(status=200)
        
        # Add multiple feeds
        self.feed_source.add(self.test_link, "Feed 1")
        self.feed_source.add("http://example.com/rss", "Feed 2")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.pprint()
            output = mock_stdout.getvalue()
            
            # Check that both feeds are printed
            self.assertIn("Feed Name: Feed 1", output)
            self.assertIn("Feed Name: Feed 2", output)
            self.assertIn(f"Feed Link: {self.test_link}", output)
            self.assertIn("Feed Link: http://example.com/rss", output)
            self.assertIn("Added On:", output)
            self.assertIn("Last Updated:", output)
            self.assertIn("-" * 20, output)
    
    @patch('feedparser.parse')
    def test_pprint_specific_feed(self, mock_parse):
        """Test printing a specific feed."""
        mock_parse.return_value = Mock(status=200)
        
        self.feed_source.add(self.test_link, self.test_name)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.pprint(self.test_name)
            output = mock_stdout.getvalue()
            
            self.assertIn(f"Feed Name: {self.test_name}", output)
            self.assertIn(f"Feed Link: {self.test_link}", output)
            self.assertIn("Added On:", output)
            self.assertIn("Last Updated:", output)
            # Should not contain separator since only one feed is printed
            self.assertNotIn("-" * 20, output)
    
    def test_pprint_nonexistent_feed(self):
        """Test printing a feed that doesn't exist."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.pprint("Nonexistent Feed")
            output = mock_stdout.getvalue()
            self.assertIn("The feed Nonexistent Feed was not found in the list.", output)
            
    def test_pprint_empty_feed_list_with_specific_name(self):
        """Test printing a specific feed when no feeds exist."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.pprint("Some Feed")
            output = mock_stdout.getvalue()
            # Should show not found message
            self.assertIn("The feed Some Feed was not found in the list.", output)
    
    @patch('feedparser.parse')
    def test_save_and_load_feeds(self, mock_parse):
        """Test saving and loading feeds to/from pickle file."""
        mock_parse.return_value = Mock(status=200)
        
        # Add some feeds
        self.feed_source.add(self.test_link, "Feed 1")
        self.feed_source.add("http://example.com/rss", "Feed 2")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filepath = temp_file.name
        
        try:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                self.feed_source.save(temp_filepath)
                output = mock_stdout.getvalue()
                self.assertIn(f"Feed list saved to {temp_filepath}.", output)
            
            # Create new FeedSource and load
            new_feed_source = FeedSource()
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                new_feed_source.load(temp_filepath)
                output = mock_stdout.getvalue()
                self.assertIn(f"Feed list loaded from {temp_filepath}.", output)
            
            # Verify loaded data
            self.assertEqual(len(new_feed_source._feeds), 2)
            self.assertEqual(len(new_feed_source._feed_names), 2)
            self.assertIn("Feed 1", new_feed_source._feed_names)
            self.assertIn("Feed 2", new_feed_source._feed_names)
            
            # Check feed details
            feed_names = [feed.name for feed in new_feed_source._feeds]
            self.assertIn("Feed 1", feed_names)
            self.assertIn("Feed 2", feed_names)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
    
    def test_load_nonexistent_file(self):
        """Test loading from a file that doesn't exist."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.load("nonexistent_file.pkl")
            output = mock_stdout.getvalue()
            self.assertIn("The file nonexistent_file.pkl was not found.", output)
    
    def test_load_corrupted_file(self):
        """Test loading from a corrupted file."""
        # Create a temporary file with invalid pickle data
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("This is not pickle data")
            temp_filepath = temp_file.name
        
        try:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                self.feed_source.load(temp_filepath)
                output = mock_stdout.getvalue()
                self.assertIn("An error occurred while loading the file:", output)
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
    
    def test_save_to_invalid_path(self):
        """Test saving to an invalid file path."""
        invalid_path = "/invalid/path/that/does/not/exist/file.pkl"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.feed_source.save(invalid_path)
            output = mock_stdout.getvalue()
            self.assertIn("An error occurred while saving the file:", output)
    
    @patch('feedparser.parse')
    def test_fetch_existing_feed(self, mock_parse):
        """Test fetching an existing feed."""
        # Setup mock for adding feed
        mock_parse.return_value = Mock(status=200)
        self.feed_source.add(self.test_link, self.test_name)
        
        # Setup mock for fetching feed
        mock_feed_data = Mock()
        mock_feed_data.entries = [{'title': 'Test Article', 'link': 'http://example.com/article'}]
        mock_parse.return_value = mock_feed_data
        
        result = self.feed_source.fetch(self.test_name)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_feed_data)
        mock_parse.assert_called_with(self.test_link)
    
    def test_fetch_nonexistent_feed(self):
        """Test fetching a feed that doesn't exist."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = self.feed_source.fetch("Nonexistent Feed")
            output = mock_stdout.getvalue()
            
            self.assertIsNone(result)
            self.assertIn("The feed Nonexistent Feed was not found in the list.", output)
    
    @patch('feedparser.parse')
    def test_fetch_with_multiple_feeds(self, mock_parse):
        """Test fetching when multiple feeds exist."""
        mock_parse.return_value = Mock(status=200)
        
        # Add multiple feeds
        self.feed_source.add(self.test_link, "Feed 1")
        self.feed_source.add("http://example.com/rss", "Feed 2")
        
        # Setup mock for fetching specific feed
        mock_feed_data = Mock()
        mock_parse.return_value = mock_feed_data
        
        result = self.feed_source.fetch("Feed 2")
        
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_feed_data)
        # Should be called with the correct feed's link
        mock_parse.assert_called_with("http://example.com/rss")
    
    def test_fetch_with_inconsistent_data_structure(self):
        """Test fetch when feed name exists in _feed_names but not in _feeds (edge case)."""
        # Manually create an inconsistent state (this shouldn't happen in normal usage)
        self.feed_source._feed_names.append("Inconsistent Feed")
        # Don't add corresponding feed to _feeds list
        
        result = self.feed_source.fetch("Inconsistent Feed")
        
        # Should return None because feed object is not found in _feeds
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
