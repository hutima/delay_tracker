import unittest
from datetime import datetime, timezone
import pipeline
class PipelineTests(unittest.TestCase):
 def setUp(self): self.rows=pipeline.make_rows(datetime(2026,8,11,12,tzinfo=timezone.utc))
 def test_grid_count(self): self.assertEqual(len(self.rows),10*3*35)
 def test_dates_targets_and_t4(self):
  self.assertEqual({r['target_date'] for r in self.rows},{f'2026-08-{d:02}' for d in range(5,15)})
  self.assertEqual(sum(r['is_final_t4']=='true' for r in self.rows),30)
 def test_embargo_and_cadence(self): pipeline.validate(self.rows)
 def test_no_outcomes_in_predictions(self): self.assertTrue(all(not r['actual_outcome'] for r in self.rows))
if __name__=='__main__': unittest.main()
