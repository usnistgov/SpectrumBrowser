package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;
import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Button;

import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.DataView;
import com.googlecode.gwt.charts.client.corechart.ScatterChart;
import com.googlecode.gwt.charts.client.corechart.ScatterChartOptions;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.Legend;
import com.googlecode.gwt.charts.client.options.LegendPosition;
import com.googlecode.gwt.charts.client.options.VAxis;

import com.sksamuel.gwt.websockets.Websocket;
import com.sksamuel.gwt.websockets.WebsocketListenerExt;


public class SystemMonitor extends AbstractSpectrumBrowserWidget implements WebsocketListenerExt, SpectrumBrowserScreen, SpectrumBrowserCallback<String> {

	private Websocket websocket;
	private VerticalPanel verticalPanel;
	private HorizontalPanel resourcePanel;
	private HorizontalPanel titlePanel;
	private HorizontalPanel buttonPanel;
	boolean isFrozen = false;
	HTML html;
	
	boolean chartApiLoaded = false;
	
	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	private static final String END_LABEL = "Service Monitor";
	
	private Button freezeButton;
	private Button logoutButton;

	public SystemMonitor(Admin admin) {
		super();
		try {
			this.admin = admin;	
			verticalPanel = new VerticalPanel();
			buttonPanel = new HorizontalPanel();
			resourcePanel = new HorizontalPanel();
			titlePanel = new HorizontalPanel();
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting server", th);
			Window.alert("Problem contacting server");
			admin.logoff();
		}
	}
	
	private void drawMenuItems() {
		
		HTML title;
		title = new HTML("<h3> The usage, by service, of various resources is shown below </h3>");
		titlePanel.add(title);
		verticalPanel.add(titlePanel);

		freezeButton = new Button("Freeze");

		freezeButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {

				isFrozen = !isFrozen;
				if (isFrozen) {
					freezeButton.setText("Unfreeze");
				} else {
					freezeButton.setText("Freeze");
				}
			}
		});
		
		buttonPanel.add(freezeButton);

	}
	
	@Override
	public void draw() {
		try {
			verticalPanel.clear();
			drawMenuItems();
			verticalPanel.setTitle("Click on canvas to freeze/unfreeze");
						
			ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

			chartLoader.loadApi(new Runnable() {
				@Override
				public void run() {
					chartApiLoaded = true;

				}
			});
			
			openWebSocket();
			
			logoutButton = new Button("Log Out");
			logoutButton.addClickHandler(new ClickHandler() {
				@Override
				public void onClick(ClickEvent event) {
					admin.logoff();
				}
			});

			buttonPanel.add(logoutButton);
			verticalPanel.add(resourcePanel);
			verticalPanel.add(buttonPanel);
		
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "ERROR drawing screen", th);
		}

	}

	@Override
	public void onMessage(String msg) {
		try {
			//  input style => msg = "<CPU>:<VirtMem>:<Disk>:"
			String[] msgArray = msg.split(":");
			
			int seconds = 60; // show the last minute of data
			
			String[] keys = Defines.RESOURCE_KEYS;
			
			DataTable[] resourceDataTableArray = new DataTable[keys.length];
			ScatterChart resourcePlot = new ScatterChart();;
			ScatterChartOptions resourcePlotOptions = null;
			int keyIndex = 0;			

			for (String key : keys){
				
				double resourceValue = Double.parseDouble(msgArray[keyIndex]);
				
				resourcePanel.add(resourcePlot);
				
				if (chartApiLoaded && resourceDataTableArray[keyIndex] == null) {
					resourceDataTableArray[keyIndex] = DataTable.create();
					resourcePlotOptions = ScatterChartOptions.create();
					resourcePlotOptions.setBackgroundColor("#f0f0f0");
					resourcePlotOptions.setPointSize(5);
					HAxis haxis = HAxis.create("Time (sec)");
					haxis.setMaxValue(seconds);
					haxis.setMinValue(0);
					resourcePlotOptions.setHAxis(haxis);
					VAxis vaxis = VAxis.create(key +" %");
					vaxis.setMaxValue(100.0);
					vaxis.setMinValue(0);
					resourcePlotOptions.setVAxis(vaxis);
					Legend legend = Legend.create();
					legend.setPosition(LegendPosition.NONE);
					resourcePlotOptions.setLegend(legend);
	
					resourcePlot.setPixelSize(800, 400); //TODO: test size
					resourcePlot.setTitle(key);
	
					resourceDataTableArray[keyIndex].addColumn(ColumnType.NUMBER,"Time (sec)");
					resourceDataTableArray[keyIndex].addRows(seconds);
	
					DataView dataView = DataView.create(resourceDataTableArray[keyIndex]);

					for (int i = 0; i < seconds; i++) {
						resourceDataTableArray[keyIndex].setCell(0, i, i, i
								+ " sec");
						resourceDataTableArray[keyIndex].setCell(1, i, resourceValue, resourceValue + " % usage");
						resourcePlot.draw(dataView, resourcePlotOptions);
					}
				}
//need to know the data table/data view translates to the plot (row/col assignment looks backwards)
				if (!isFrozen) {
					if (resourceDataTableArray[keyIndex] != null) {
						resourceDataTableArray[keyIndex].removeRow(0);
						resourceDataTableArray[keyIndex].addRow();
						int rowCount = resourceDataTableArray[keyIndex].getNumberOfRows();
	
						for (int i = 0; i < seconds; i++) {
							resourceDataTableArray[keyIndex].setCell(i, 0, i, i + " sec");
						}
						resourceDataTableArray[keyIndex].setCell(rowCount - 1, 1, resourceValue, resourceValue + " % usage");
						
						resourcePlot.redraw();
	
						resourcePlot.draw(resourceDataTableArray[keyIndex]);
					}
				}
				keyIndex++;
			}
		} catch (Throwable ex) {
			logger.log(Level.SEVERE, "ERROR parsing data ", ex);
		}
	}

	@Override
	public void onOpen() {
		logger.finer("onOpen");
		String sid = Admin.getSessionToken();
		String token = sid;
		websocket.send(token);
	}
	
	@Override
	public void onClose() {
		logger.fine("websocket.onClose");
		websocket.close();
	}

	@Override
	public void onError() {
		logger.info("Web Socket Error");
		websocket.close();
		try {
			openWebSocket();
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Could not re-open websocket", th);
				
		}

	}

	private void openWebSocket() {

		String authority = Admin.getBaseUrlAuthority();
		String url;
		logger.finer("openWebSocket: resource Usage with authority "
				+ authority);
		if (authority.startsWith("https")) {
			url = authority.replace("https", "wss") + "/admin/sysmonitor";
		} else {
			url = authority.replace("http", "ws") + "/admin/sysmonitor";
		}
		logger.fine("Websocket URL " + url);
		websocket = new Websocket(url);
		websocket.addListener(this);
		if (!Websocket.isSupported()) {
			Window.alert("Websockets not supported on this browser");
			draw();
		} else {
			websocket.open();
		}

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
