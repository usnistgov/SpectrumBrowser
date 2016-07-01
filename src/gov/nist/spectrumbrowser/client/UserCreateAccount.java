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

import java.util.logging.Level;
import java.util.logging.Logger;

import gov.nist.spectrumbrowser.client.SpectrumBrowser;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

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
 * Screen for user to create a new login account
 * @author Julie Kub /\ KH
 *
 */
public class UserCreateAccount implements SpectrumBrowserScreen {
	private VerticalPanel verticalPanel;
	private SpectrumBrowser spectrumBrowser;
	private Button sendButton, cancelButton;
	private MyHandler handler = new MyHandler();
	public static final String LABEL = "Create Account";
	private TextBox emailEntry, lastNameEntry, firstNameEntry;
	private PasswordTextBox passwordEntry, passwordEntryConfirm;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public UserCreateAccount(VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser) {
		logger.finer("UserCreateAccount");
		this.verticalPanel = verticalPanel;
		this.spectrumBrowser = spectrumBrowser;
	}
	
	public void draw() {
		Window.setTitle("MSOD:Request Account");
		verticalPanel.clear();
		HTML title = new HTML("<h2>Request Account </h2>");
		verticalPanel.add(title);
		
		Grid grid = new Grid(5,2);
		
		grid.setText(0, 0, "Email Address");
		emailEntry = new TextBox();
		emailEntry.setWidth("250px");
		emailEntry.addKeyDownHandler(handler);
		grid.setWidget(0, 1, emailEntry);
		
		grid.setText(1, 0, "First Name");
		firstNameEntry = new TextBox();
		firstNameEntry.setWidth("250px");
		firstNameEntry.addKeyDownHandler(handler);
		grid.setWidget(1,1,firstNameEntry);
		
		grid.setText(2,0, "Last Name");		
		lastNameEntry = new TextBox();
		lastNameEntry.setWidth("250px");
		lastNameEntry.addKeyDownHandler(handler);
		grid.setWidget(2, 1, lastNameEntry);
		
		grid.setText(3,0, "Password");		
		passwordEntry = new PasswordTextBox();
		passwordEntry.setWidth("250px");
		passwordEntry.addKeyDownHandler(handler);
		grid.setWidget(3, 1, passwordEntry);
		
		grid.setText(4,0, "Re-type password");		
		passwordEntryConfirm = new PasswordTextBox();
		passwordEntryConfirm.setWidth("250px");
		passwordEntryConfirm.addKeyDownHandler(handler);
		grid.setWidget(4, 1, passwordEntryConfirm);
		verticalPanel.add(grid);
		
		grid.getCellFormatter().addStyleName(0, 0, "alignMagic");
		grid.getCellFormatter().addStyleName(1, 0, "alignMagic");
		grid.getCellFormatter().addStyleName(2, 0, "alignMagic");
		grid.getCellFormatter().addStyleName(3, 0, "alignMagic");
		grid.getCellFormatter().addStyleName(4, 0, "alignMagic");
			
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
	
	private void createHandler() {
		String firstName, lastName, emailAddress, password, confirmPassword;
		firstName = lastName = emailAddress = password = confirmPassword = "";
		
		firstName = firstNameEntry.getValue().trim();
		lastName = lastNameEntry.getValue().trim();
		emailAddress = emailEntry.getValue().trim();
		password = passwordEntry.getValue();
		confirmPassword = passwordEntryConfirm.getValue();
				
		logger.finer("CreateAccount: " + emailAddress);
		if (firstName == null || firstName.length() == 0) {
			Window.alert("First Name with at least one character is required.");
			return;
		}
		if (lastName == null || lastName.length() == 0) {
			Window.alert("Last Name with at least one character is required.");
			return;
		}

		if (emailAddress == null || emailAddress.length() == 0) {
			Window.alert("Email is required.");
			return;
		}

		if (password == null || password.length() == 0) {
			Window.alert("Password is required.");
			return;
		}
		if (confirmPassword == null || confirmPassword.length() == 0) {
			Window.alert("Re-typed password is required.");
			return;
		}
		if (password != confirmPassword)
		{
			Window.alert("Password entries must match.");
			return;					
		}

		JSONObject jsonObject  = new JSONObject();
		jsonObject.put(Defines.ACCOUNT_EMAIL_ADDRESS, new JSONString(emailAddress));
		jsonObject.put(Defines.ACCOUNT_FIRST_NAME, new JSONString(firstName));
		jsonObject.put(Defines.ACCOUNT_LAST_NAME, new JSONString(lastName));
		jsonObject.put(Defines.ACCOUNT_PASSWORD, new JSONString(password));
		jsonObject.put(Defines.ACCOUNT_PRIVILEGE, new JSONString(Defines.USER_PRIVILEGE));

		spectrumBrowser.getSpectrumBrowserService().requestNewAccount(jsonObject.toString(), new SpectrumBrowserCallback<String>(){

			@Override
			public void onSuccess(String result) {
				try {
					JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
					String status = jsonObject.get(Defines.STATUS).isString().stringValue();
					String statusMessage = jsonObject.get(Defines.STATUS_MESSAGE).isString().stringValue();
					if (status.equals("FORWARDED")) {
						Window.alert(statusMessage);
						verticalPanel.clear();
						spectrumBrowser.draw();
					} else {
						Window.alert(statusMessage);
						if (status.equals("INVALEMAIL")) {
							emailEntry.setText("");
						}else if (status.equals("INVALPASS")) {
							passwordEntry.setText("");
							passwordEntryConfirm.setText("");
						}else if (status.equals("INVALFNAME")) {
							firstNameEntry.setText("");
						}else if (status.equals("INVALLNAME")) {
							lastNameEntry.setText("");
						}
					}
				}
			    catch (Throwable th) {
			    	Window.alert("Could not parse the JSON message.");
				}
			}

			@Override
			public void onFailure(Throwable throwable) {
				logger.log(Level.SEVERE, "Error occured when contacting server in UserCreateAccount",throwable);
				Window.alert("Error occured contacting server in UserCreateAccount.");
			}
		});
					
				
			}
		
	private class MyHandler implements ClickHandler, KeyDownHandler {
		@Override
		public void onKeyDown(KeyDownEvent event) {
			if(event.getNativeKeyCode() == KeyCodes.KEY_ENTER) {
				createHandler();
			}
		}

		@Override
		public void onClick(ClickEvent event) {
			if(sendButton == event.getSource()) {
				createHandler();
			}
			
			if(cancelButton == event.getSource()) {
				verticalPanel.clear();
				spectrumBrowser.draw();
			}
		}
	}

	@Override
	public String getLabel() {
		return LABEL;
	}

	@Override
	public String getEndLabel() {
		// TODO Auto-generated method stub
		return null;
	}
}
