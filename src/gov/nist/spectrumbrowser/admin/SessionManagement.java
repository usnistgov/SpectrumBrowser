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
package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;
import gov.nist.spectrumbrowser.admin.AdminService;

public class SessionManagement extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserCallback<String>, SpectrumBrowserScreen {

	private Admin admin;
	private static final Logger logger = Logger.getLogger("SpectrumBrowser");
	private JSONArray userSessions;
	private JSONArray adminSessions;
	private boolean redraw = false;
	private boolean frozen = false;
	private String freezeRequester;
	private  Timer timer;

	public SessionManagement(Admin admin) {
		this.admin = admin;
		this.redraw = true;
		try {
			Admin.getAdminService().getSessions(this);
		} catch (Exception ex) {
			if (timer != null) {
				timer.cancel();
			}
			admin.logoff();
		}
	}

	@Override
	public void draw() {
		try {
			verticalPanel.clear();
			HTML title = new HTML("<h2>Active Sessions </h2>");
			verticalPanel.add(title);
			if (frozen) {
				HTML subtitle = new HTML(
						"<h3>New session creation is temporarily suspended by "
								+ freezeRequester
								+ ". Users cannot use the system.</h3>");
				verticalPanel.add(subtitle);
			}

			int nrows = userSessions.size() + adminSessions.size();
			Grid grid = new Grid(nrows + 1, 5);
			for (int i = 0; i < grid.getRowCount(); i++) {
				for (int j = 0; j < grid.getColumnCount(); j++) {
					grid.getCellFormatter().setHorizontalAlignment(i, j,
							HasHorizontalAlignment.ALIGN_CENTER);
					grid.getCellFormatter().setVerticalAlignment(i, j,
							HasVerticalAlignment.ALIGN_MIDDLE);
				}
			}

			for (int i = 0; i < grid.getColumnCount(); i++) {
				grid.getCellFormatter().setStyleName(0, i, "textLabelStyle");
			}
			grid.setBorderWidth(2);
			grid.setCellSpacing(2);
			grid.setCellPadding(2);
			grid.setText(0, 0, "Email Address");
			grid.setText(0, 1, "Remote IP Address");
			grid.setText(0, 2, "Session Start Time");
			grid.setText(0, 3, "Session End Time");
			grid.setText(0, 4, "User Privilege");

			for (int i = 0; i < userSessions.size(); i++) {
				JSONObject jsonObj = userSessions.get(i).isObject();
				String userName = jsonObj.get(Defines.USER_NAME).isString()
						.stringValue();
				int row = i + 1;
				grid.setText(row, 0, userName);
				String ipAddr = jsonObj.get(Defines.REMOTE_ADDRESS).isString()
						.stringValue();
				grid.setText(row, 1, ipAddr);
				String startTime = jsonObj.get(Defines.SESSION_LOGIN_TIME)
						.isString().stringValue();
				grid.setText(row, 2, startTime);
				String expiryTime = jsonObj.get(Defines.EXPIRE_TIME).isString()
						.stringValue();
				grid.setText(row, 3, expiryTime);
				grid.setText(row, 4, "user");

			}
			for (int i = 0; i < adminSessions.size(); i++) {
				JSONObject jsonObj = adminSessions.get(i).isObject();
				int row = i + userSessions.size() + 1;
				String userName = jsonObj.get(Defines.USER_NAME).isString()
						.stringValue();
				grid.setText(row, 0, userName);
				String ipAddr = jsonObj.get(Defines.REMOTE_ADDRESS).isString()
						.stringValue();
				grid.setText(row, 1, ipAddr);
				String startTime = jsonObj.get(Defines.SESSION_LOGIN_TIME)
						.isString().stringValue();
				grid.setText(row, 2, startTime);
				String expiryTime = jsonObj.get(Defines.EXPIRE_TIME).isString()
						.stringValue();
				grid.setText(row, 3, expiryTime);
				grid.setText(row, 4, "admin");
			}
			verticalPanel.add(grid);

			HorizontalPanel hpanel = new HorizontalPanel();

			Button freezeButton = new Button("Freeze Sessions");
			hpanel.add(freezeButton);
			freezeButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					boolean yesno = Window
							.confirm("Warning! No new sessions will be allowed.\n "
									+ "Email will be sent to the administrator when all active sessions are terminated.\n Proceed?");
					if (yesno) {
						SessionManagement.this.redraw = true;
						Admin.getAdminService().freezeSessions(
								SessionManagement.this);
					}
				}
			});

			Button unfreezeButton = new Button("Cancel Freeze");

			hpanel.add(unfreezeButton);
			unfreezeButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					SessionManagement.this.redraw = true;
					Admin.getAdminService().unfreezeSessions(
							SessionManagement.this);

				}
			});

			Button logoffButton = new Button("Log Off");
			hpanel.add(logoffButton);
			logoffButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					timer.cancel();
					admin.logoff();
				}
			});
			verticalPanel.add(hpanel);
			timer = new Timer() {
				@Override
				public void run() {
					if (Admin.getSessionToken() != null) {
						SessionManagement.this.redraw = true;
						Admin.getAdminService().getSessions(
								SessionManagement.this);
					}
				}

			};

			timer.schedule(5 * 1000);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error drawing", th);
			admin.logoff();
		}

	}

	@Override
	public String getLabel() {
		return null;
	}

	@Override
	public String getEndLabel() {
		return "Sessions";
	}

	@Override
	public void onSuccess(String result) {
		try {
			JSONObject jsonObject = (JSONObject) JSONParser
					.parseLenient(result);
			String status = jsonObject.get(Defines.STATUS).isString()
					.stringValue();
			if (status.equals(Defines.OK)) {
				//logger.finer("Sessions = " + result);
				userSessions = jsonObject.get(Defines.USER_SESSIONS).isArray();
				adminSessions = jsonObject.get(Defines.ADMIN_SESSIONS)
						.isArray();
				frozen = jsonObject.get(Defines.FROZEN).isBoolean()
						.booleanValue();
				freezeRequester = jsonObject.get(Defines.FREEZE_REQUESTER)
						.isString().stringValue();
				logger.finer("userSessionsSize = " + userSessions.size()
						+ " adminSessionsSize = " + adminSessions.size());
				if (redraw)
					draw();
			}
		} catch (Throwable th) {
			admin.logoff();
		}

	}

	@Override
	public void onFailure(Throwable throwable) {
		admin.logoff();
	}
	
	public  void cancelTimer() {
		timer.cancel();
	}

}
