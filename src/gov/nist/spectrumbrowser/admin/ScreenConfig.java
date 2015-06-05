package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class ScreenConfig extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserScreen, SpectrumBrowserCallback<String> {

	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private Grid grid;
	
	private JSONValue jsonValue;
	private JSONObject jsonObject;
	private Button logoutButton;
	private Button applyButton;
	private Button cancelButton;
	private boolean redraw = false;
	
	private HorizontalPanel titlePanel;


	public ScreenConfig(Admin admin) {
		super();
		try {
			this.admin = admin;
			Admin.getAdminService().getScreenConfig(this);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting server", th);
			Window.alert("Problem contacting server");
			admin.logoff();
		}

	}

	@Override
	public void onSuccess(String jsonString) {
		try {
			jsonValue = JSONParser.parseLenient(jsonString);
			jsonObject = jsonValue.isObject();
			if (redraw) {
				draw();
			}
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error Parsing JSON message", th);
			admin.logoff();
		}

	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error Communicating with server message",
				throwable);
		admin.logoff();
	}
	
	private void setInteger(int row, String key, String fieldName, TextBox widget) {
		grid.setText(row, 0, fieldName);
		int value = super.getAsInt(jsonValue, key);
		widget.setText(Integer.toString(value));
		grid.setWidget(row, 1, widget);
	}

	@Override
	public void draw() {
		verticalPanel.clear();
		HTML title;
		title = new HTML("<h3>Please enter your desired parameters</h3>");

		// THE DESCRIPTION IN THE CONFIG INTERFACE HAS A FIX: 
		// CHART IN THE CODE IS SPECTROGRAM IN THE DESCRIPTION; 
		// CHART IN THE CODE MODIFIES THE SPECTROGRAM CONFIG, AND VICE VERSA
		
		titlePanel = new HorizontalPanel();
		titlePanel.add(title);
		verticalPanel.add(titlePanel);
		
		grid = new Grid(8, 2);
		grid.setCellSpacing(4);
		grid.setBorderWidth(2);
		verticalPanel.add(grid);

		for (int i = 0; i < grid.getRowCount(); i++) {
			for (int j = 0; j < grid.getColumnCount(); j++) {
				grid.getCellFormatter().setHorizontalAlignment(i, j,
						HasHorizontalAlignment.ALIGN_CENTER);
				grid.getCellFormatter().setVerticalAlignment(i, j,
						HasVerticalAlignment.ALIGN_MIDDLE);
			}
		}
		grid.setCellPadding(2);
		grid.setCellSpacing(2);
		grid.setBorderWidth(2);

		int index = 0;
		
		TextBox mapWidth = new TextBox();
		mapWidth.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 400)
						newVal = 400;
					else if (newVal > 1600)
						newVal = 1600;
					
					jsonObject.put(Defines.MAP_WIDTH, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 400 and 1600");
				}
			}});
		setInteger(index++,Defines.MAP_WIDTH,"Map Width",mapWidth);
		
		
		TextBox mapHeight = new TextBox();
		mapHeight.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 400)
						newVal = 400;
					else if (newVal > 1600)
						newVal = 1600;
					
					jsonObject.put(Defines.MAP_HEIGHT, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 400 and 1600");
				}
			}});
		setInteger(index++,Defines.MAP_HEIGHT,"Map Height",mapHeight);
		
		
		TextBox specWidth = new TextBox();
		specWidth.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 400)
						newVal = 400;
					else if (newVal > 1600)
						newVal = 1600;
					
					jsonObject.put(Defines.SPEC_WIDTH, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 400 and 1600");
				}
			}});
		setInteger(index++,Defines.SPEC_WIDTH,"Chart Width",specWidth);
		
		
		TextBox specHeight = new TextBox();
		specHeight.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 400)
						newVal = 400;
					else if (newVal > 1600)
						newVal = 1600;
					
					jsonObject.put(Defines.SPEC_HEIGHT, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 400 and 1600");
				}
			}});
		setInteger(index++,Defines.SPEC_HEIGHT,"Chart Height",specHeight);
		
		
		TextBox chartWidth = new TextBox();
		chartWidth.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 1)
						newVal = 1;
					else if (newVal > 10)
						newVal = 10;
					
					jsonObject.put(Defines.CHART_WIDTH, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 1 and 10");
				}
			}});
		setInteger(index++,Defines.CHART_WIDTH, "Spectrogram Width", chartWidth);
		
		
		TextBox chartHeight = new TextBox();
		chartHeight.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 1)
						newVal = 1;
					else if (newVal > 10)
						newVal = 10;
					
					jsonObject.put(Defines.CHART_HEIGHT, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 1 and 10");
				}
			}});
		setInteger(index++,Defines.CHART_HEIGHT, "Spectrogram Height", chartHeight);
		
		
		TextBox canvWidth = new TextBox();
		canvWidth.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 400)
						newVal = 400;
					else if (newVal > 1600)
						newVal = 1600;
					
					jsonObject.put(Defines.CANV_WIDTH, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 400 and 1600");
				}
			}});
		setInteger(index++,Defines.CANV_WIDTH, "Spec Canvas Width", canvWidth);
		
		
		TextBox canvHeight = new TextBox();
		canvHeight.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String str = event.getValue();
				try {
					int newVal = Integer.parseInt(str);
					
					if (newVal < 400)
						newVal = 400;
					else if (newVal > 1600)
						newVal = 1600;
					
					jsonObject.put(Defines.CANV_HEIGHT, new JSONNumber(newVal));
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter a valid integer between 400 and 1600");
				}
			}});
		setInteger(index++,Defines.CANV_HEIGHT, "Spec Canvas Height", canvHeight);
		
		

		for (int i = 0; i < grid.getRowCount(); i++) {
			grid.getCellFormatter().setStyleName(i, 0, "textLabelStyle");
		}
		
		applyButton = new Button("Apply Changes");
		cancelButton = new Button("Cancel Changes");
		logoutButton = new Button("Log Out");

		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				
				Admin.getAdminService().setScreenConfig(jsonObject.toString(),
						new SpectrumBrowserCallback<String>() {

							@Override
							public void onSuccess(String result) {
								JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
								if (jsonObj.get("status").isString().stringValue().equals("OK")) {
									Window.alert("Configuration successfully updated");
								} else {
									String errorMessage = jsonObj.get("ErrorMessage").isString().stringValue();
									Window.alert("Error in updating config - please re-enter. Error Message : "+errorMessage);
								}
							}

							@Override
							public void onFailure(Throwable throwable) {
								Window.alert("Error communicating with server");
								admin.logoff();
							}
						});
			}
		});
		

		cancelButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				redraw = true;
				Admin.getAdminService().getScreenConfig(ScreenConfig.this);
			}
		});

		logoutButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}
		});

		HorizontalPanel buttonPanel = new HorizontalPanel();
		buttonPanel.add(applyButton);
		buttonPanel.add(cancelButton);
		buttonPanel.add(logoutButton);
		verticalPanel.add(buttonPanel);
	
	}
	
	@Override
	public String getLabel() {
		return null;
	}
	
	@Override
	public String toString() {
		return null;
	}

	@Override
	public String getEndLabel() {
		return "Screen Config";
	}

}