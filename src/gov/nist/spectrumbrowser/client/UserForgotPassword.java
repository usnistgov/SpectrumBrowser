/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.KeyCodes;
import com.google.gwt.event.dom.client.KeyDownEvent;
import com.google.gwt.event.dom.client.KeyDownHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Screen for user to reset their password if they have forgotten it.
 * @author Julie Kub /\ KH
 *
 */
public class UserForgotPassword implements SpectrumBrowserScreen {
	private TextBox emailEntry;
	private VerticalPanel verticalPanel;
	private SpectrumBrowser spectrumBrowser;
	private Button sendButton, cancelButton;
	private MyHandler handler = new MyHandler();
	public static final String LABEL = "Reset Password";
	private PasswordTextBox passwordEntry, passwordEntryConfirm;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
		
	public UserForgotPassword(VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser) {
		logger.finer("UserResetPassword");
		this.verticalPanel = verticalPanel;
		this.spectrumBrowser = spectrumBrowser;
	}
	
	public void draw() {
		Window.setTitle("MSOD:Reset Password");
		verticalPanel.clear();
		HTML title = new HTML("<h2>Reset Password</h2>");
		verticalPanel.add(title);
		
		Grid grid = new Grid(3,2);
		
		grid.setText(0, 0, "Email Address");
		emailEntry = new TextBox();
		emailEntry.setWidth("250px");
		emailEntry.addKeyDownHandler(handler);
		grid.setWidget(0, 1, emailEntry);
		
		grid.setText(1,0, "New Password");
		passwordEntry = new PasswordTextBox();
		passwordEntry.setWidth("250px");
		passwordEntry.addKeyDownHandler(handler);
		grid.setWidget(1, 1, passwordEntry);
		
		grid.setText(2,0, "Re-type New Password");
		passwordEntryConfirm = new PasswordTextBox();
		passwordEntryConfirm.setWidth("250px");
		passwordEntryConfirm.addKeyDownHandler(handler);
		grid.setWidget(2, 1, passwordEntryConfirm);
		verticalPanel.add(grid);	
		
		grid.getCellFormatter().addStyleName(0, 0, "alignMagic");
		grid.getCellFormatter().addStyleName(1, 0, "alignMagic");
		grid.getCellFormatter().addStyleName(2, 0, "alignMagic");
	
		Grid buttonGrid = new Grid(1,2);
		verticalPanel.add(buttonGrid);
		
		sendButton = new Button("Submit");
		sendButton.addStyleName("sendButton");
		buttonGrid.setWidget(0,0,sendButton);
		sendButton.addClickHandler(handler);
		
		cancelButton = new Button("Cancel");
		buttonGrid.setWidget(0, 1, cancelButton);
		cancelButton.addClickHandler(handler);
	}
	
	private void forgotHandler() {
			String password = "";
			String passwordConfirm = "";
			String emailAddress = "";
			try {
				password = passwordEntry.getValue();
				passwordConfirm = passwordEntryConfirm.getValue();
				emailAddress = emailEntry.getValue().trim();					
			}
			catch (Throwable th) {
				//not a problem, since we will check for null's below.
			}			
			logger.finer("SubmitNewAccount: " + emailAddress);
			if (emailAddress == null || emailAddress.length() == 0) {
				Window.alert("Email is required.");
				return;
			}
			if (password == null || password.length() == 0) {
				Window.alert("Password is required.");
				return;
			}
			if (passwordConfirm == null || passwordConfirm.length() == 0) {
				Window.alert("Re-typed password is required.");
				return;
			}
			if (password != passwordConfirm)
			{
				Window.alert("Password entries must match.");
				return;					
			}
			JSONObject jsonObject  = new JSONObject();
			jsonObject.put(Defines.ACCOUNT_EMAIL_ADDRESS, new JSONString(emailAddress));
			jsonObject.put(Defines.ACCOUNT_NEW_PASSWORD, new JSONString(password));
			jsonObject.put(Defines.ACCOUNT_PRIVILEGE, new JSONString(Defines.USER_PRIVILEGE));
			
			spectrumBrowser.getSpectrumBrowserService().requestNewPassword(jsonObject.toString(), new SpectrumBrowserCallback<String>(){
				@Override
				public void onSuccess(String result) {
					JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
					String statusMessage = jsonObject.get(Defines.STATUS_MESSAGE).isString().stringValue();
					Window.alert(statusMessage);	
					verticalPanel.clear();
					spectrumBrowser.draw();	
				}

				@Override
				public void onFailure(Throwable throwable) {
					logger.log(Level.SEVERE, "Error occured when contacting server in UserForgotPassword",throwable);
					Window.alert("Error occured contacting server in UserForgotPassword.");
				}
			});
}
	
	private class MyHandler implements ClickHandler, KeyDownHandler {
		@Override
		public void onKeyDown(KeyDownEvent event) {
			if(event.getNativeKeyCode() == KeyCodes.KEY_ENTER) {
				forgotHandler();
			}
		}

		@Override
		public void onClick(ClickEvent event) {
			if(sendButton == event.getSource()) {
				forgotHandler();
			}
			
			if(cancelButton == event.getSource()) {
				verticalPanel.clear();
				spectrumBrowser.draw();
			}
		}
	}

	@Override
	public String getLabel() {
		return null;
	}

	@Override
	public String getEndLabel() {
		// TODO Auto-generated method stub
		return null;
	}

}
