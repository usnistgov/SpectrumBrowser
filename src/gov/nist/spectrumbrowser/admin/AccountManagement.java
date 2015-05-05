package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;
import gov.nist.spectrumbrowser.common.Defines;

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

	
	private class TogglePrivilegeValueChangeHandler implements ValueChangeHandler<Boolean> {
		String emailAddress;

		public TogglePrivilegeValueChangeHandler( String emailAddress) {
			this.emailAddress = emailAddress;
		}
		
		@Override
		public void onValueChange(ValueChangeEvent<Boolean> event) {
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
		HTML html = new HTML("<h2>User Accounts</h2>");
		int rows = userAccounts.size();
		verticalPanel.add(html);
		grid = new Grid(rows+1,11);
		grid.setText(0, 0, "Email Adddress");
		grid.setText(0, 1, "First Name");
		grid.setText(0, 2, "Last Name");
		grid.setText(0, 3, "Admin Privilege");
		grid.setText(0, 4, "Failed Login Attempts");
		grid.setText(0, 5, "Account Locked?");
		grid.setText(0, 6, "Unlock Account");
		grid.setText(0, 7, "Password Expiry Date");
		grid.setText(0, 8, "Reset Expiration");
		grid.setText(0, 9, "Creation Date");
		grid.setText(0, 10, "Delete Account");
		// TODO: add session information like currently logged in, time logged in, time session expires 
		// & ability to delete a session object 
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		for (int i = 1; i < rows+1; i++) {
			JSONObject account = userAccounts.get(i-1).isObject();
			grid.setText(i, 0, account.get(Defines.ACCOUNT_EMAIL_ADDRESS).isString().stringValue());
			grid.setText(i, 1, account.get(Defines.ACCOUNT_FIRST_NAME).isString().stringValue());
			grid.setText(i, 2, account.get(Defines.ACCOUNT_LAST_NAME).isString().stringValue());
			String priv = account.get(Defines.ACCOUNT_PRIVILEGE).isString().stringValue();
			CheckBox togglePrivilege = new CheckBox();
			togglePrivilege.setValue(priv.equals("admin"));
			togglePrivilege.addValueChangeHandler( new TogglePrivilegeValueChangeHandler(account.get(Defines.ACCOUNT_EMAIL_ADDRESS).isString().stringValue()));
			grid.setWidget(i, 3, togglePrivilege);
			grid.setText(i, 4, Integer.toString((int) account.get(Defines.ACCOUNT_NUM_FAILED_LOGINS).isNumber().doubleValue()));
			grid.setText(i, 5, Boolean.toString(account.get(Defines.ACCOUNT_LOCKED).isBoolean().booleanValue()));
			Button unlock = new Button("Unlock");
			unlock.addClickHandler( new UnlockClickHandler(account.get(Defines.ACCOUNT_EMAIL_ADDRESS).isString().stringValue()));
			grid.setWidget(i, 6, unlock);
			//JEK: note: the 'datePasswordExpires' and 'dateAccountCreated' are not in accounts database since we store time in seconds.
			// These date fields are just for display here so we do not need to define constants for JSON strings.
			grid.setText(i,  7, account.get("datePasswordExpires").isString().stringValue());
			Button reset = new Button("Reset Expiration");
			reset.addClickHandler( new ResetExpirationClickHandler(account.get(Defines.ACCOUNT_EMAIL_ADDRESS).isString().stringValue()));
			grid.setWidget(i, 8, reset);
			grid.setText(i,  9, account.get("dateAccountCreated").isString().stringValue());
			Button delete = new Button("Delete");
			delete.addClickHandler( new DeleteClickHandler(account.get(Defines.ACCOUNT_EMAIL_ADDRESS).isString().stringValue()));
			grid.setWidget(i, 10, delete);
		}
		
		for (int i = 0; i < grid.getColumnCount(); i++) {
			grid.getCellFormatter().setStyleName(0, i, "textLabelStyle");
		}
		
		
		for (int i = 0; i < grid.getRowCount(); i++) {
			for (int j = 0; j < grid.getColumnCount(); j++) {
				grid.getCellFormatter().setHorizontalAlignment(i, j,
						HasHorizontalAlignment.ALIGN_CENTER);
				grid.getCellFormatter().setVerticalAlignment(i, j,
						HasVerticalAlignment.ALIGN_MIDDLE);
			}
		}
		
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button addAccountButton = new Button ("Add");
		addAccountButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				//JEK: I commented out this line because we not want to go back to account management if add account failed
				//redraw = true;
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
		return "User Accounts";
	}
	
	public void setUserAccounts(JSONArray userAccounts) {
		this.userAccounts = userAccounts;
	}

	@Override
	public void onSuccess(String result) {
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			userAccounts = jsonValue.isObject().get(Defines.USER_ACCOUNTS).isArray();	
			logger.finer("Returned " + userAccounts.size());
			String serverStatus = jsonValue.isObject().get(Defines.STATUS).isString().stringValue();
			String serverStatusMessage = jsonValue.isObject().get(Defines.STATUS_MESSAGE).isString().stringValue();
			logger.finer("serverStatus " + serverStatus);
			logger.finer("serverStatusMessage " + serverStatusMessage);
			
			if (serverStatus != "OK"){
				Window.alert(serverStatusMessage);
			}

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
