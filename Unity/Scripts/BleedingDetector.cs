using UnityEngine;
using System.Collections;

public class BleedingDetector : MonoBehaviour
{
    private bool isBleeding = false;
    private float bleedTime = 0f;

    void Update()
    {
        // TEMP: press 'B' to simulate detection
        if (Input.GetKeyDown(KeyCode.B))
        {
            ToggleBleeding();
        }

        if (isBleeding)
        {
            bleedTime += Time.deltaTime;
            if (bleedTime > 2f)
            {
                Debug.Log("⚠️ Heavy bleeding detected. Initiating compression guidance...");
                // TODO: trigger AR overlay or sound alert
                bleedTime = 0f;
            }
        }
    }

    private void ToggleBleeding()
    {
        isBleeding = !isBleeding;
        bleedTime = 0f;
        Debug.Log(isBleeding ? "Bleeding simulation started." : "Bleeding simulation stopped.");
    }
}
