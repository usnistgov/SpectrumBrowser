package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.Button;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;


public class ServiceControl extends AbstractSpectrumBrowserWidget implements SpectrumBrowserScreen, SpectrumBrowserCallback<String> {

	private HorizontalPanel titlePanel;
	private Grid grid;
	HTML html;
	
	private TextBox[] statusBoxArray;
	private TextBox AdminBox;
	private TextBox SpecBrowBox;
	private TextBox StreamBox;
	private TextBox OccuBox;
	private TextBox SysMonBox;
	private static String[] SERVICE_NAMES = Defines.SERVICE_NAMES;
	private static int NUM_SERVICES = Defines.SERVICE_NAMES.length;
	private static int STATUS_CHECK_TIME_SEC = 5;
	
	private Button[] stopButtonArray;
	private Button[] restartButtonArray;
	private boolean[] buttonEnabledArray;

	
	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	private static final String END_LABEL = "Service Control";

	public ServiceControl(Admin admin) {
		super();
		try {
			this.admin = admin;	
			titlePanel = new HorizontalPanel();
			statusBoxArray = new TextBox[NUM_SERVICES];
			stopButtonArray = new Button[NUM_SERVICES];
			restartButtonArray = new Button[NUM_SERVICES];
			buttonEnabledArray = new boolean[NUM_SERVICES];
			AdminBox = new TextBox();
			SpecBrowBox = new TextBox();
			StreamBox = new TextBox();
			OccuBox = new TextBox();
			SysMonBox = new TextBox();
			statusBoxArray[0] = AdminBox;
			statusBoxArray[1] = SpecBrowBox;
			statusBoxArray[2] = StreamBox;
			statusBoxArray[3] = OccuBox;
			statusBoxArray[4] = SysMonBox;
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting server", th);
			Window.alert("Problem contacting server");
			admin.logoff();
		}
	}
	
	private void drawMenuItems() {
		HTML title;
		title = new HTML("<h3> The statuses of the project services are shown below </h3>");
		titlePanel.add(title);
		verticalPanel.add(titlePanel);		
	}
	
	@Override
	public void draw() {
		try {
			verticalPanel.clear();
			titlePanel.clear();			
			drawMenuItems();
			
			grid = new Grid(NUM_SERVICES + 1, 4);
			grid.setCellSpacing(4);
			grid.setBorderWidth(2);
			verticalPanel.add(grid);
			
			grid.setText(0, 0, "Service");
			grid.setText(0, 1, "Status");
			grid.setText(0, 2, "Stop");
			grid.setText(0, 3, "Restart");
			
			for (int i = 0; i < NUM_SERVICES; i++) {
				grid.setText(i + 1, 0, SERVICE_NAMES[i]);
				grid.setWidget(i + 1, 1, statusBoxArray[i]);
				if (i!=0){
					createStopButton(i);
					createRestartButton(i);
					grid.setWidget(i + 1, 2, stopButtonArray[i]);
					grid.setWidget(i + 1, 3, restartButtonArray[i]);
				}
				else{
					grid.setText(i + 1, 2, "N/A");
					grid.setText(i + 1, 3, "N/A");
				}
			}
			
			setStatusBox();
			
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "ERROR drawing service control screen", th);
		}
	}
	
	private void setStatusBox() {
		
	    Timer timer = new Timer() {

	    	String status = "";
	        @Override
	        public void run() {
	        	for (int i = 0; i < NUM_SERVICES; i++) {
	    			Admin.getAdminService().getServiceStatus(SERVICE_NAMES[i], new SpectrumBrowserCallback<String>() {
	    				@Override
						public void onSuccess(String result) {
							JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
							if (jsonObj.get("status").isString().stringValue().equals("OK")) {
								status = jsonObj.get("serviceStatus").isString().stringValue();
							} else {
								String errorMessage = jsonObj.get("ErrorMessage").isString().stringValue();
								Window.alert("Error getting service status. Please refresh. Error Message : "+errorMessage);
								status = "ERROR";
							}
						}

						@Override
						public void onFailure(Throwable throwable) {
							Window.alert("Error communicating with server");
							admin.logoff();
						}
	    			});
	    			statusBoxArray[i].setText(status);
	    			buttonEnabledArray[i] = true;
	    		}
	        }
	    };
	    timer.scheduleRepeating(STATUS_CHECK_TIME_SEC*1000);
	}
	
	public void createStopButton(final int i){
		Button stopButton = new Button();
		stopButton.removeStyleName("gwt-Button");
		stopButton.getElement().getStyle().setBackgroundColor("red");
		stopButton.setHeight("50px");
		stopButton.setWidth("50px");
		buttonEnabledArray[i] = true;
		stopButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				if(buttonEnabledArray[i]){
				
					Admin.getAdminService().stopService(SERVICE_NAMES[i],
							new SpectrumBrowserCallback<String>() {
	
								@Override
								public void onSuccess(String result) {
									JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
									if (jsonObj.get("status").isString().stringValue().equals("OK")) {
										Window.alert("Service successfully stopped");
									} else {
										String errorMessage = jsonObj.get("ErrorMessage").isString().stringValue();
										Window.alert("Error stopping service. Please refresh. Error Message : "+errorMessage);
									}
								}
	
								@Override
								public void onFailure(Throwable throwable) {
									Window.alert("Error communicating with server");
									admin.logoff();
								}
					});
					buttonEnabledArray[i] = false;
				}
			}
		});
		stopButtonArray[i] = stopButton;
	}
	
	public void createRestartButton(final int i){
		Button restartButton = new Button();
		restartButton.removeStyleName("gwt-Button");
		restartButton.getElement().getStyle().setBackgroundColor("green");
		restartButton.setHeight("50px");
		restartButton.setWidth("50px");
		buttonEnabledArray[i] = true;
		restartButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				if(buttonEnabledArray[i]){
					Admin.getAdminService().restartService(SERVICE_NAMES[i],
							new SpectrumBrowserCallback<String>() {
	
								@Override
								public void onSuccess(String result) {
									JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
									if (jsonObj.get("status").isString().stringValue().equals("OK")) {
										Window.alert("Service successfully restarted");
									} else {
										String errorMessage = jsonObj.get("ErrorMessage").isString().stringValue();
										Window.alert("Error restarting service. Please refresh. Error Message : "+errorMessage);
									}
								}
	
								@Override
								public void onFailure(Throwable throwable) {
									Window.alert("Error communicating with server");
									admin.logoff();
								}
							});
					buttonEnabledArray[i] = false;
				}
			}
		});
		restartButtonArray[i] = restartButton;
	}

	@Override
	public String getLabel() {
		return END_LABEL + " >>";
	}

	@Override
	public String getEndLabel() {
		return END_LABEL;
	}

	@Override
	public void onSuccess(String jsonString) {}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error Communicating with server",
				throwable);
		admin.logoff();
	}
	
	@Override
	public String toString() {
		return null;
	}

}
