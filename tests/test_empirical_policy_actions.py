import copy
import unittest

from scripts.empirical_policy_actions import allocate,SCORED_POLICIES


class PolicyActionTests(unittest.TestCase):
    def keys(self,n):return [("hotpotqa","bm25",f"invented-{i:05}") for i in range(n)]
    def scores(self,keys,eligible):return {p:{k:-1. if k in eligible else None for k in keys} for p in SCORED_POLICIES}

    def test_negative_ties_use_canonical_keys_and_keep_is_empty(self):
        keys=list(reversed(self.keys(30)));eligible=set(keys);scores=self.scores(keys,eligible)
        result=allocate(keys,eligible,scores)
        self.assertEqual(result["cap"],2)
        self.assertEqual(result["selected"]["HGB"],set(sorted(keys)[:2]))
        self.assertEqual(result["selected"]["Keep"],set())
        self.assertTrue(all(result["replacement_counts"][p]==2 for p in SCORED_POLICIES))

    def test_ineligible_rows_stay_in_denominator_and_insufficient_eligible_is_retained(self):
        keys=self.keys(30);eligible={keys[-1]}
        result=allocate(keys,eligible,self.scores(keys,eligible))
        self.assertEqual((result["N_all"],result["N_eligible"],result["cap"]),(30,1,2))
        self.assertEqual(result["selected"]["GbV"],eligible)
        self.assertEqual(len(result["ledger"]),30)
        empty=allocate(keys,set(),self.scores(keys,set()))
        self.assertTrue(all(x==0 for x in empty["replacement_counts"].values()))
        ten=self.keys(10)
        self.assertEqual(allocate(ten,set(ten),self.scores(ten,set(ten)))["cap"],0)

    def test_primary_18000_has_900_global_switches_without_dataset_quota(self):
        keys=[(d,r,f"invented-{i:04}") for d in ("hotpotqa","2wikimultihopqa","musique")
              for r in ("bm25","dense","hybrid") for i in range(2000)]
        scores={p:{k:1. if k[0]=="hotpotqa" else -1. for k in keys} for p in SCORED_POLICIES}
        result=allocate(keys,set(keys),scores)
        self.assertEqual(result["cap"],900)
        for p in SCORED_POLICIES:
            self.assertEqual(len(result["selected"][p]),900)
            self.assertTrue(all(k[0]=="hotpotqa" for k in result["selected"][p]))

    def test_policy_specific_missing_nonfinite_and_unmasked_scores_are_rejected(self):
        keys=self.keys(30);eligible=set(keys);scores=self.scores(keys,eligible)
        for bad in (None,float('nan'),float('inf'),True,'1'):
            changed=copy.deepcopy(scores);changed['HGB'][keys[0]]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):allocate(keys,eligible,changed)
        with self.assertRaises(ValueError):allocate(keys,eligible-{keys[0]},scores)
        changed=copy.deepcopy(scores);del changed['V2'][keys[0]]
        with self.assertRaises(ValueError):allocate(keys,eligible,changed)


if __name__=='__main__':unittest.main()
