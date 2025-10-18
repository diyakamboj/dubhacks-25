using UnityEngine;

public class VoiceTrigger : MonoBehaviour
{
    public HUDManager hudManager;

    void Update()
    {
        // Simulated voice trigger (press V to mimic saying "Call 911")
        if (Input.GetKeyDown(KeyCode.V))
        {
            hudManager.ShowInstruction("Voice command detected: Calling 911...");
        }
    }
}
