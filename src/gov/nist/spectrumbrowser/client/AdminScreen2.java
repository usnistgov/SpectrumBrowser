package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Sample admin screen.
 * @author local
 *
 *Note: this is a sample admin screen class. It is structured in the same
 *way as the other screens (i.e. it implements SpectrumBrowserCallback). 
 *Right now it does nothing useful.
 */
class AdminScreen2 implements SpectrumBrowserCallback {
	
	private VerticalPanel verticalPanel;
	private SpectrumBrowser spectrumBrowser;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	
	public AdminScreen2(VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser) {
		logger.finer("AdminScreen2");
		this.verticalPanel = verticalPanel;
		this.spectrumBrowser = spectrumBrowser;
	}
	

	public void draw() {
		

		verticalPanel.clear();
		MenuBar menuBar = new MenuBar();
		SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();
		menuBar.addItem(
				safeHtml.appendEscaped(SpectrumBrowser.LOGOFF_LABEL)
						.toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						spectrumBrowser.logoff();

					}
				});
		menuBar.addItem("AdminScreen", new Command(){
		      @Override
		      public void execute() {
		    	  new AdminScreen(verticalPanel, AdminScreen2.this.spectrumBrowser).draw();
		      }
		});
		

		verticalPanel.add(menuBar);

		spectrumBrowser.getSpectrumBrowserService().getAdminBand(
				spectrumBrowser.getSessionId(), "LTE",
				new SpectrumBrowserCallback<String>() {

					@Override
					public void onFailure(Throwable caught) {
						logger.log(Level.SEVERE,
								"Error in processing request", caught);
						spectrumBrowser.logoff();
					}

					@Override
					public void onSuccess(String jsonString) {
						JSONValue jsonValue = JSONParser.parseStrict(jsonString);
						JSONObject jsonObject = jsonValue.isObject();
						JSONObject mpar = jsonValue.isObject().get("freqRange").isObject();
						double minFreqMHz = (mpar.get("minFreqHz").isNumber().doubleValue() / 1E6);
						double maxFreqMHz = (mpar.get("maxFreqHz").isNumber().doubleValue() / 1E6);

						HorizontalPanel bandNameField = new HorizontalPanel();
						Label bandLabel = new Label("Band Name");
						bandLabel.setWidth("150px");
						bandNameField.add(bandLabel);
						TextBox textBoxName = new TextBox();
						textBoxName.setWidth("150px");
						textBoxName.setText(jsonObject.get("bandName").isString().stringValue());
						bandNameField.add(textBoxName);
						verticalPanel.add(bandNameField);
						
						HorizontalPanel bandThrehsoldField = new HorizontalPanel();
						Label bandThrehsoldLabel = new Label("Band Occupancy Threshold");
						bandThrehsoldLabel.setWidth("150px");
						bandThrehsoldField.add(bandThrehsoldLabel);
						TextBox textBoxThreshold = new TextBox();
						textBoxThreshold.setText(jsonObject.get("occupancyThresdholddBm").isNumber().toString());
						bandThrehsoldField.add(textBoxThreshold);
						verticalPanel.add(bandThrehsoldField);
						
						HorizontalPanel bandminFreqField = new HorizontalPanel();
						Label minFreqLabel = new Label("Min Frequency (MHz)");
						minFreqLabel.setWidth("150px");
						bandminFreqField.add(minFreqLabel);
						TextBox textBoxMinFreqMHz = new TextBox();
						textBoxMinFreqMHz.setText(new Double(minFreqMHz).toString());
						bandminFreqField.add(textBoxMinFreqMHz);
						verticalPanel.add(bandminFreqField);
						
						HorizontalPanel bandmaxFreqField = new HorizontalPanel();
						Label maxFreqLabel = new Label("Max Frequency (MHz)");
						maxFreqLabel.setWidth("150px");
						bandmaxFreqField.add(maxFreqLabel);
						TextBox textBoxMaxFreqMHz = new TextBox();
						textBoxMaxFreqMHz.setText(new Double(maxFreqMHz).toString());
						bandmaxFreqField.add(textBoxMaxFreqMHz);
						verticalPanel.add(bandmaxFreqField);
					}
				}
		);
		
		
	}

	@Override
	public void onSuccess(Object result) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub
		
	}

}
