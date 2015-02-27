package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.Date;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.i18n.client.DateTimeFormat;


import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class AccountManagement extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserCallback<String>, SpectrumBrowserScreen {

	private Admin admin;
	private JSONArray userAccounts;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private Grid grid;
	private boolean redraw;
	
	private class UnlockClickHandler implements ClickHandler {
		String emailAddress;

		public UnlockClickHandler( String emailAddress) {
			this.emailAddress = emailAddress;
		}
		
		@Override
		public void onClick(ClickEvent event) {
			redraw = true;
			try {
				logger.finer("Email Address to unlock " + emailAddress);
				Admin.getAdminService().unlockAccount(emailAddress,AccountManagement.this);
			} catch ( Throwable th) {
				logger.log(Level.SEVERE, "Error communicating with server",th);
				Window.alert("error communicating with server");
				admin.logoff();
			}
		}}	

	
	private class TogglePrivilegeClickHandler implements ClickHandler {
		String emailAddress;

		public TogglePrivilegeClickHandler( String emailAddress) {
			this.emailAddress = emailAddress;
		}
		
		@Override
		public void onClick(ClickEvent event) {
			redraw = true;
			try {
				logger.finer("Email Address to toggle privilege for: " + emailAddress);
				Admin.getAdminService().togglePrivilegeAccount(emailAddress,AccountManagement.this);
			} catch ( Throwable th) {
				logger.log(Level.SEVERE, "Error communicating with server",th);
				Window.alert("error communicating with server");
				admin.logoff();
			}
		}}

	private class ResetExpirationClickHandler implements ClickHandler {
		String emailAddress;

		public ResetExpirationClickHandler( String emailAddress) {
			this.emailAddress = emailAddress;
		}
		
		@Override
		public void onClick(ClickEvent event) {
			redraw = true;
			try {
				logger.finer("Email Address to reset expiration " + emailAddress);
				Admin.getAdminService().resetAccountExpiration(emailAddress,AccountManagement.this);
			} catch ( Throwable th) {
				logger.log(Level.SEVERE, "Error communicating with server",th);
				Window.alert("error communicating with server");
				admin.logoff();
			}
		}}
	
	private class DeleteClickHandler implements ClickHandler {
		String emailAddress;

		public DeleteClickHandler( String emailAddress) {
			this.emailAddress = emailAddress;
		}
		
		@Override
		public void onClick(ClickEvent event) {
			redraw = true;
			try {
				logger.finer("Email Address to delete " + emailAddress);
				Admin.getAdminService().deleteAccount(emailAddress,AccountManagement.this);
			} catch ( Throwable th) {
				logger.log(Level.SEVERE, "Error communicating with server",th);
				Window.alert("error communicating with server");
				admin.logoff();
			}
		}}
	
	public AccountManagement(Admin admin) {
		logger.finer("AccountManagement");
		try {
			this.admin = admin;
			Admin.getAdminService().getUserAccounts(this);
			logger.finer("Accounts Retrieved");
		} catch (Throwable th) {
			Window.alert("Problem contacting server when initializing Account Management");
			logger.log(Level.SEVERE,"Problem contacting server", th);
			admin.logoff();
		}
	}
	

	@Override
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<h2>Account Management</h2>");
		int rows = userAccounts.size();
		verticalPanel.add(html);
		grid = new Grid(rows+1,12);
		grid.setText(0, 0, "Email Adddress");
		grid.setText(0, 1, "First Name");
		grid.setText(0, 2, "Last Name");
		grid.setText(0, 3, "Privilege");
		grid.setText(0, 4, "Toggle Privilege");
		grid.setText(0, 5, "Failed Login Attempts");
		grid.setText(0, 6, "Account Locked?");
		grid.setText(0, 7, "Unlock Account");
		grid.setText(0, 8, "Date Password Expires");
		grid.setText(0, 9, "Reset Expiration");
		grid.setText(0, 10, "Date Account Created");
		grid.setText(0, 11, "Delete Account");
		// TODO: add session information like currently logged in, time logged in, time session expires 
		// & ability to delete a session object 
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		for (int i = 1; i < rows+1; i++) {
			JSONObject account = userAccounts.get(i-1).isObject();
			grid.setText(i, 0, account.get("emailAddress").isString().stringValue());
			grid.setText(i, 1, account.get("firstName").isString().stringValue());
			grid.setText(i, 2, account.get("lastName").isString().stringValue());
			grid.setText(i, 3, account.get("privilege").isString().stringValue());
			Button togglePrivilege = new Button("Toggle Privilege");
			togglePrivilege.addClickHandler( new TogglePrivilegeClickHandler(account.get("emailAddress").isString().stringValue()));
			grid.setWidget(i, 4, togglePrivilege);
			grid.setText(i, 5, Integer.toString((int) account.get("numFailedLoginAttempts").isNumber().doubleValue()));
			grid.setText(i, 6, Boolean.toString(account.get("accountLocked").isBoolean().booleanValue()));
			Button unlock = new Button("Unlock Account");
			unlock.addClickHandler( new UnlockClickHandler(account.get("emailAddress").isString().stringValue()));
			grid.setWidget(i, 7, unlock);
			grid.setText(i,  8, account.get("datePasswordExpires").isString().stringValue());
			Button reset = new Button("Reset Expiration");
			reset.addClickHandler( new ResetExpirationClickHandler(account.get("emailAddress").isString().stringValue()));
			grid.setWidget(i, 9, reset);
			grid.setText(i,  10, account.get("dateAccountCreated").isString().stringValue());
			Button delete = new Button("Delete Account");
			delete.addClickHandler( new DeleteClickHandler(account.get("emailAddress").isString().stringValue()));
			grid.setWidget(i, 11, delete);


		}
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button addAccountButton = new Button ("Add");
		addAccountButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				redraw = true;
				new AddAccount(admin, AccountManagement.this, verticalPanel).draw();
			}});
		buttonPanel.add(addAccountButton);
		Button logoffButton = new Button("Log Off");
		
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		buttonPanel.add(logoffButton);
		verticalPanel.add(buttonPanel);
	
	}

	@Override
	public String getLabel() {
		return null;
	}

	@Override
	public String getEndLabel() {
		return "Account Management";
	}

	@Override
	public void onSuccess(String result) {
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			userAccounts = jsonValue.isObject().get("userAccounts").isArray();	
			logger.finer("Returned " + userAccounts.size());
			String serverAction = "";
			String statusValue = "";
			try {
				serverAction = jsonValue.isObject().get("action").isString().stringValue();
				statusValue = jsonValue.isObject().get("status").isString().stringValue();
			}
			catch(Throwable th) {
				//This not a problem, since getting user accounts does not have action or status with JSON:
				serverAction = "getAccounts";
				statusValue = "OK";
			}
			logger.finer("serverAction " + serverAction);
			logger.finer("status " + statusValue);
			

			String windowAlert = "";
			switch(statusValue){
				case "EXISTING":
					windowAlert = "An account already exists for this email address.";	
					break;
				case "LASTADMIN":
					windowAlert = "Last admin account, cannot perform operation or no admin accounts left.";	
					break;
				case "INVALUSER":
					windowAlert="Account not found.";	
					break;							
				case "INVALEMAIL":
					windowAlert="Your new email is invalid.";	
					break;
				case "INVALFNAME":
					windowAlert= "Your first name is invalid.";	
					break;
				case "INVALLNAME":
					windowAlert="Your last name is invalid.";	
					break;
				case "INVALPRIV":
					windowAlert="Your privilege is invalid.";	
					break;
				case "NOK":
					windowAlert ="There was an issue on the server, please check the system logs.";	
					break;
				case "OK": 
					windowAlert ="";	
					break;
				default:
					windowAlert ="Unknown status returned from the server: "+statusValue;
					break;
			}
			if (windowAlert != "")
			{
				Window.alert(windowAlert);	
			}
			logger.finer("window alert: "+windowAlert);

			if (redraw) {
				this.draw();
			}
		} catch (Throwable th) {
			Window.alert("Error parsing returned JSON");
			logger.log(Level.SEVERE, "Problem parsing JSON", th);
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		Window.alert("Error communicating with server in Account Management");
		logger.log(Level.SEVERE, "Error communicating with server", throwable);
		admin.logoff();
	}

}
