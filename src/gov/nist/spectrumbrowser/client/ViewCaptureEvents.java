package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserScreen;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.ListBox;
import com.google.gwt.user.datepicker.client.DateBox;
import com.google.gwt.user.datepicker.client.DatePicker;

public class ViewCaptureEvents extends AbstractSpectrumBrowserScreen implements SpectrumBrowserCallback<String> {

	private SpectrumBrowser spectrumBrowser;
	private VerticalPanel verticalPanel;
	
	private HTML title;
	private HorizontalPanel hpanel;
	private String END_LABEL = "View Capture Events";
	private String sys2detect;
	private ArrayList<SpectrumBrowserScreen> navigation;
	private DatePicker calendar;
	private int dayCount;
	private long tSelectedStartTime;
	private String sensorId;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public ViewCaptureEvents(String sensorId, long tSelectedStartTime, int dayCount,
			String sys2detect, long minFreq, long maxFreq, VerticalPanel verticalPanel,
			SpectrumBrowser spectrumBrowser,
			ArrayList<SpectrumBrowserScreen> navigation) {
		super.setNavigation(verticalPanel, navigation, spectrumBrowser, END_LABEL);
		this.navigation = new ArrayList<SpectrumBrowserScreen>(navigation);
		this.navigation.add(this);
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
		this.dayCount = dayCount;
		this.tSelectedStartTime = tSelectedStartTime;
		this.sensorId = sensorId;
		this.sys2detect = sys2detect;
		spectrumBrowser.getSpectrumBrowserService().getCaptureEvents(sensorId, tSelectedStartTime, 1,this);
	}
	
	

	public void draw() {
		verticalPanel.clear();
		super.drawNavigation();
	}


	@Override
	public void onSuccess(String result) {
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			JSONObject jsonObject = jsonValue.isObject();
			String status = jsonObject.get("status").isString().stringValue();
			
			if (! status.equals("OK")) {
				String errorMessage = jsonObject.get("ErrorMessage").isString().stringValue();
				Window.alert("Error Processing Request: " + errorMessage);
				return;
			}

			JSONArray eventTimes = jsonObject.get("events").isArray();
			logger.finer("Found " + eventTimes.size() + " capture events.");

			title = new HTML("<h2>Capture Events</h2>");
			verticalPanel.add(title);

			String labelHtml = "<p>  A <b>capture event</b> is an event of interest detected by the sensor that triggers the capture "
					+ "and recording of baseband I/Q  data which is stored on the sensor host.";
			labelHtml += "A use case for capture events is identifying the source of interference for an incumbent system.</p> ";
			
			HTML label = new HTML(labelHtml);
			label.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_JUSTIFY);
			verticalPanel.add(label);
			
			Button prevDay = new Button("Previous Day");
			Button nextDay = new Button("Next Day");

			HorizontalPanel hpanel = new HorizontalPanel();
			hpanel.add(prevDay);
			hpanel.add(nextDay);
			verticalPanel.add(hpanel);

			ListBox captureEventList = new ListBox();
			for (int i=0; i<eventTimes.size(); i++) {
				
				String eventTime = eventTimes.get(i).isObject().get("formattedTimeStamp").isString().stringValue();
				captureEventList.addItem(eventTime);
			}
			captureEventList.setVisibleItemCount(20);
			verticalPanel.add(captureEventList);
			//calendar = new DatePicker();
			//hpanel.add(calendar);

		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error parsing json file ", th);
		}

	}

	@Override
	public void onFailure(Throwable throwable) {
		Window.alert("Error contacting web service");
	}

}
