from pywinauto.application import Application

# Main
if __name__ == "__main__":
    app = Application()
    app.start('notepad.exe C:\\Speakers\\horns\\calibration-results\\test.txt')
    confirmWin = app.window(title_re = u'Notepad') #Check your window header object name.
    # Use timeout based on average pop up time in your application.
    if confirmWin.exists(timeout=2, retry_interval=1): 
        confirmWin.set_focus()
        yesBtn = confirmWin[u'&Yes'] 
        # Check the object name of the Yes button.
        yesBtn.click()
        print('Saved new file.')
    elif app.Notepad.exists(timeout=2, retry_interval=1):
        app.Notepad.set_focus()
        print('File already exists.')
    else:
        print('No matching windows found.')
    # Need to be able to focus window for this to work
    app.Notepad.Edit.type_keys("Hi from Python interactive prompt %s" % str(dir()), with_spaces = True)
    app.Notepad.menu_select("File -> Save")
    app.Notepad.menu_select("File -> Exit")
