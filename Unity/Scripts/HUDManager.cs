using UnityEngine;
using UnityEngine.UI;

public class HUDManager : MonoBehaviour
{
    public Text instructionText;
    public Button call911Button;
    public AudioSource metronomeAudio;

    void Start()
    {
        call911Button.onClick.AddListener(Call911);
    }

    public void ShowInstruction(string text)
    {
        instructionText.text = text;
        instructionText.gameObject.SetActive(true);
    }

    public void StartMetronome()
    {
        metronomeAudio.loop = true;
        metronomeAudio.Play();
    }

    public void StopMetronome()
    {
        metronomeAudio.Stop();
    }

    private void Call911()
    {
        Debug.Log("Calling 911...");
        ShowInstruction("Calling 911...");
    }
}