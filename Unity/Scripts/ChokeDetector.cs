using UnityEngine;
using System.Collections;

public class ChokeDetector : MonoBehaviour
{
    private bool isChoking = false;
    private float detectionTime = 0f;

    void Update()
    {
        // TEMP: press 'C' to simulate detection
        if (Input.GetKeyDown(KeyCode.C))
        {
            ToggleChoking();
        }

        if (isChoking)
        {
            detectionTime += Time.deltaTime;
            if (detectionTime > 2f)
            {
                Debug.Log("⚠️ Possible choking detected. Triggering first aid sequence...");
                // TODO: trigger AR guidance or CV event
                detectionTime = 0f;
            }
        }
    }

    private void ToggleChoking()
    {
        isChoking = !isChoking;
        detectionTime = 0f;
        Debug.Log(isChoking ? "Choking simulation started." : "Choking simulation stopped.");
    }
}
