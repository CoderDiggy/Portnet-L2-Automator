"""
Test Input Validation for Analyze Function
Verify that random/nonsensical inputs are filtered out
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ''))

from simple_main import validate_incident_input

async def test_input_validation():
    """Test that random inputs are correctly filtered out"""
    print("🧪 Testing AI-Powered Input Validation...")
    print("🛡️ Filtering out nonsensical inputs while allowing legitimate incidents")
    
    # Test cases - Invalid inputs that should be rejected
    invalid_inputs = [
        {
            "input": "asdf",
            "description": "Random keystrokes"
        },
        {
            "input": "hello world",
            "description": "Simple greeting"
        },
        {
            "input": "test",
            "description": "Single test word"
        },
        {
            "input": "qwerty123",
            "description": "Random keyboard pattern"
        },
        {
            "input": "lol this is funny",
            "description": "Casual conversation"
        },
        {
            "input": "aaaaaaaaaaa",
            "description": "Repeated characters"
        },
        {
            "input": "how are you doing today?",
            "description": "Personal question"
        },
        {
            "input": "pizza time!",
            "description": "Food reference"
        },
        {
            "input": "hjkl;'",
            "description": "Keyboard mashing"
        },
        {
            "input": "meme content here",
            "description": "Meme text"
        }
    ]
    
    # Test cases - Valid inputs that should be accepted
    valid_inputs = [
        {
            "input": "Container CMAU123456 showing duplicate entries in PORTNET system causing delays",
            "description": "Container system issue"
        },
        {
            "input": "EDI message processing failure, getting ERROR status on all incoming messages",
            "description": "EDI system problem"
        },
        {
            "input": "Vessel berth allocation system down, unable to assign berths to incoming vessels",
            "description": "Vessel management issue"
        },
        {
            "input": "Critical equipment failure at Terminal 3 crane, operations stopped",
            "description": "Equipment malfunction"
        },
        {
            "input": "Network connectivity issues preventing access to port management system",
            "description": "Network problem"
        },
        {
            "input": "Safety incident at loading dock, worker injury reported, area cordoned off",
            "description": "Safety incident"
        },
        {
            "input": "Cargo manifest discrepancy found, container contents don't match documentation",
            "description": "Documentation issue"
        }
    ]
    
    print(f"\n🚫 Testing {len(invalid_inputs)} Invalid Inputs (should be rejected):")
    invalid_results = []
    
    for i, test_case in enumerate(invalid_inputs, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"   Input: \"{test_case['input']}\"")
        
        try:
            result = await validate_incident_input(test_case['input'])
            
            expected_valid = False  # These should be rejected
            actual_valid = result["valid"]
            status = "✅ PASS" if actual_valid == expected_valid else "❌ FAIL"
            
            print(f"   Result: {'Accepted' if actual_valid else 'Rejected'} (Expected: Rejected) - {status}")
            if not actual_valid:
                print(f"   Reason: {result['reason']}")
            
            invalid_results.append({
                "test": i,
                "passed": actual_valid == expected_valid,
                "description": test_case['description']
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            invalid_results.append({
                "test": i,
                "passed": False,
                "error": str(e)
            })
    
    print(f"\n✅ Testing {len(valid_inputs)} Valid Inputs (should be accepted):")
    valid_results = []
    
    for i, test_case in enumerate(valid_inputs, 1):
        print(f"\n🚨 Test {i}: {test_case['description']}")
        print(f"   Input: \"{test_case['input'][:60]}{'...' if len(test_case['input']) > 60 else ''}\"")
        
        try:
            result = await validate_incident_input(test_case['input'])
            
            expected_valid = True  # These should be accepted
            actual_valid = result["valid"]
            status = "✅ PASS" if actual_valid == expected_valid else "❌ FAIL"
            
            print(f"   Result: {'Accepted' if actual_valid else 'Rejected'} (Expected: Accepted) - {status}")
            if not actual_valid:
                print(f"   Rejection Reason: {result['reason']}")
            
            valid_results.append({
                "test": i,
                "passed": actual_valid == expected_valid,
                "description": test_case['description']
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            valid_results.append({
                "test": i,
                "passed": False,
                "error": str(e)
            })
    
    # Summary
    invalid_passed = sum(1 for r in invalid_results if r.get('passed', False))
    valid_passed = sum(1 for r in valid_results if r.get('passed', False))
    
    print(f"\n" + "="*70)
    print("📊 INPUT VALIDATION TEST RESULTS")
    print("="*70)
    print(f"🚫 Invalid Input Filtering: {invalid_passed}/{len(invalid_results)} passed")
    print(f"✅ Valid Input Acceptance: {valid_passed}/{len(valid_results)} passed")
    
    total_passed = invalid_passed + valid_passed
    total_tests = len(invalid_results) + len(valid_results)
    
    success_rate = (total_passed / total_tests) * 100
    print(f"🤖 AI Validation Accuracy: {total_passed}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("🎉 OUTSTANDING: Input validation is highly accurate!")
    elif success_rate >= 85:
        print("🚀 EXCELLENT: AI effectively filters nonsensical inputs!")
    elif success_rate >= 75:
        print("👍 GOOD: Input validation working well with minor issues")
    else:
        print("⚠️  NEEDS TUNING: Validation logic may need adjustment")
    
    return {
        "invalid_results": invalid_results,
        "valid_results": valid_results,
        "success_rate": success_rate
    }

if __name__ == "__main__":
    # Run the input validation test
    asyncio.run(test_input_validation())