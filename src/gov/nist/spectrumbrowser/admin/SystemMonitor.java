package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
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

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;


public class SystemMonitor extends AbstractSpectrumBrowserWidget implements WebsocketListenerExt, SpectrumBrowserScreen, SpectrumBrowserCallback<String> {

	private Websocket websocket;
	private VerticalPanel resourcePanel;
	private HorizontalPanel titlePanel;
	private Grid grid;
	HTML html;
	
	private String[] keys = Defines.RESOURCE_KEYS;
	private DataTable[] resourceDataTableArray = new DataTable[keys.length];
	
	private ScatterChart CPUPlot = null;
	private ScatterChart VirtMemPlot = null;
	private ScatterChart NetSentPlot = null;
	private ScatterChart NetRecvPlot = null;
	private ScatterChartOptions resourcePlotOptionsCPU = null;
	private ScatterChartOptions resourcePlotOptionsVMem = null;
	private ScatterChartOptions resourcePlotOptionsNetSent = null;
	private ScatterChartOptions resourcePlotOptionsNetRecv = null;
	private DataView CPUData = null;
	private DataView VirtMemData = null;
	private DataView NetSentData = null;
	private DataView NetRecvData = null;
	private int keyIndex = 0;
	
	private TextBox[] resourceBoxArray;
	private TextBox CPUBox;
	private TextBox VirtMemBox;
	private TextBox DiskBox;
	private TextBox NetSentBox;
	private TextBox NetRecvBox;
	
	private boolean chartApiLoaded = false;
	private boolean initialWebSocketOpen = true;
	private int seconds = 60; // show the last minute of data
	
	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	private static final String END_LABEL = "System Monitor";

	public SystemMonitor(Admin admin) {
		super();
		try {
			this.admin = admin;	
			resourcePanel = new VerticalPanel();
			titlePanel = new HorizontalPanel();
			resourceBoxArray = new TextBox[keys.length];
			CPUBox = new TextBox();
			VirtMemBox = new TextBox();
			DiskBox = new TextBox();
			NetSentBox = new TextBox();
			NetRecvBox = new TextBox();
			resourceBoxArray[0] = CPUBox;
			resourceBoxArray[1] = VirtMemBox;
			resourceBoxArray[2] = DiskBox;
			resourceBoxArray[3] = NetSentBox;
			resourceBoxArray[4] = NetRecvBox;
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting server", th);
			Window.alert("Problem contacting server");
			admin.logoff();
		}
	}
	
	private void drawMenuItems() {
		HTML title;
		title = new HTML("<h3> The usage of various resources is shown below </h3>");
		titlePanel.add(title);
		verticalPanel.add(titlePanel);		
	}
	
	@Override
	public void draw() {
		try {
			verticalPanel.clear();
			titlePanel.clear();
			resourcePanel.clear();
			
			drawMenuItems();
			ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

			chartLoader.loadApi(new Runnable() {
				@Override
				public void run() {
					chartApiLoaded = true;
					CPUPlot = new ScatterChart();
					VirtMemPlot = new ScatterChart();
					NetSentPlot = new ScatterChart();
					NetRecvPlot = new ScatterChart();
					CPUPlot.setPixelSize(800, 200);
					CPUPlot.setTitle(keys[0]);
					VirtMemPlot.setPixelSize(800, 200);
					VirtMemPlot.setTitle(keys[1]);
					NetSentPlot.setPixelSize(800, 200);
					NetSentPlot.setTitle(keys[3]);
					NetRecvPlot.setPixelSize(800, 200);
					NetRecvPlot.setTitle(keys[4]);
					resourcePanel.add(CPUPlot);
					resourcePanel.add(VirtMemPlot);
					resourcePanel.add(NetSentPlot);
					resourcePanel.add(NetRecvPlot);
					
					resourcePlotOptionsCPU = ScatterChartOptions.create();
					resourcePlotOptionsCPU.setBackgroundColor("#f0f0f0");
					resourcePlotOptionsCPU.setPointSize(5);
					resourcePlotOptionsVMem = ScatterChartOptions.create();
					resourcePlotOptionsVMem.setBackgroundColor("#f0f0f0");
					resourcePlotOptionsVMem.setPointSize(5);
					resourcePlotOptionsNetSent = ScatterChartOptions.create();
					resourcePlotOptionsNetSent.setBackgroundColor("#f0f0f0");
					resourcePlotOptionsNetSent.setPointSize(5);
					resourcePlotOptionsNetRecv = ScatterChartOptions.create();
					resourcePlotOptionsNetRecv.setBackgroundColor("#f0f0f0");
					resourcePlotOptionsNetRecv.setPointSize(5);
					
					HAxis haxis = HAxis.create("Time (sec)");
					haxis.setMaxValue(seconds - 1);
					haxis.setMinValue(0);
					resourcePlotOptionsCPU.setHAxis(haxis);
					resourcePlotOptionsVMem.setHAxis(haxis);
					resourcePlotOptionsNetSent.setHAxis(haxis);
					resourcePlotOptionsNetRecv.setHAxis(haxis);
					
					VAxis vaxis = VAxis.create("Usage %");
					vaxis.setMaxValue(100.0);
					vaxis.setMinValue(0);
					resourcePlotOptionsCPU.setVAxis(vaxis);
					resourcePlotOptionsVMem.setVAxis(vaxis);
					
					VAxis vaxisNet = VAxis.create("Bytes/Sec");
					resourcePlotOptionsNetSent.setVAxis(vaxisNet);
					resourcePlotOptionsNetRecv.setVAxis(vaxisNet);
					
					Legend legend = Legend.create();
					legend.setPosition(LegendPosition.NONE);
					resourcePlotOptionsCPU.setLegend(legend);
					resourcePlotOptionsVMem.setLegend(legend);
					resourcePlotOptionsNetSent.setLegend(legend);
					resourcePlotOptionsNetRecv.setLegend(legend);
					
					resourcePlotOptionsCPU.setTitle(keys[0]);
					resourcePlotOptionsVMem.setTitle(keys[1]);
					resourcePlotOptionsNetSent.setTitle(keys[3]);
					resourcePlotOptionsNetRecv.setTitle(keys[4]);
					
					resourceDataTableArray[0] = DataTable.create();
					resourceDataTableArray[0].addColumn(ColumnType.NUMBER,"Time (sec)");
					resourceDataTableArray[0].addColumn(ColumnType.NUMBER, keys[0] + " %");
					resourceDataTableArray[0].addRows(seconds);

					for (int i = 0; i < seconds; i++) {
						resourceDataTableArray[0].setCell(i, 0, i, i
								+ " sec");
						resourceDataTableArray[0].setCell(i, 1, 0, 0
								+ " %");
					}
					
					CPUData = DataView.create(resourceDataTableArray[0]);
					CPUPlot.draw(CPUData, resourcePlotOptionsCPU);
					
					resourceDataTableArray[1] = DataTable.create();
					resourceDataTableArray[1].addColumn(ColumnType.NUMBER,"Time (sec)");
					resourceDataTableArray[1].addColumn(ColumnType.NUMBER, keys[1] + " %");
					resourceDataTableArray[1].addRows(seconds);

					for (int i = 0; i < seconds; i++) {
						resourceDataTableArray[1].setCell(i, 0, i, i
								+ " sec");
						resourceDataTableArray[1].setCell(i, 1, 0, 0
								+ " %");
					}
					
					VirtMemData = DataView.create(resourceDataTableArray[1]);
					VirtMemPlot.draw(VirtMemData, resourcePlotOptionsVMem);
					
					resourceDataTableArray[3] = DataTable.create();
					resourceDataTableArray[3].addColumn(ColumnType.NUMBER,"Time (sec)");
					resourceDataTableArray[3].addColumn(ColumnType.NUMBER, keys[3] + " Bytes/Sec");
					resourceDataTableArray[3].addRows(seconds);

					for (int i = 0; i < seconds; i++) {
						resourceDataTableArray[3].setCell(i, 0, i, i
								+ " sec");
						resourceDataTableArray[3].setCell(i, 1, 0, 0
								+ " B/s");
					}
					
					NetSentData = DataView.create(resourceDataTableArray[3]);
					NetSentPlot.draw(NetSentData, resourcePlotOptionsNetSent);
					
					resourceDataTableArray[4] = DataTable.create();
					resourceDataTableArray[4].addColumn(ColumnType.NUMBER,"Time (sec)");
					resourceDataTableArray[4].addColumn(ColumnType.NUMBER, keys[4] + " Bytes/Sec");
					resourceDataTableArray[4].addRows(seconds);

					for (int i = 0; i < seconds; i++) {
						resourceDataTableArray[4].setCell(i, 0, i, i
								+ " sec");
						resourceDataTableArray[4].setCell(i, 1, 0, 0
								+ " B/s");
					}
					
					NetRecvData = DataView.create(resourceDataTableArray[4]);
					NetRecvPlot.draw(NetRecvData, resourcePlotOptionsNetRecv);
				}
			});
			
			grid = new Grid(2, 5);
			grid.setCellSpacing(4);
			grid.setBorderWidth(2);
			verticalPanel.add(grid);
			
			for (int i = 0; i < keys.length; i++) {
				grid.setWidget(1, i, resourceBoxArray[i]);
			}
			
			verticalPanel.add(resourcePanel);
			
			if(initialWebSocketOpen){
				openWebSocket();
				initialWebSocketOpen = false;
			}
		
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "ERROR drawing system monitor screen", th);
		}

	}

	@Override
	public void onMessage(String msg) {
		try {
			if(chartApiLoaded){
				//  input style => msg = "<CPU>:<VirtMem>:<Disk>:<NetSent>:<NetRecv>"
				String[] msgArray = msg.split(":");
			
				keyIndex = 0;

				for (String key : keys){
					
					double resourceValue = round(Double.parseDouble(msgArray[keyIndex]));
					
					if (keyIndex < 3)
						grid.setText(0, keyIndex, key + " (%)");
					else
						grid.setText(0, keyIndex, key + " (Bytes/Sec)");
					
					resourceBoxArray[keyIndex].setText(Double.toString(resourceValue));
					
					if (resourceDataTableArray[keyIndex] != null) {
						
						resourceDataTableArray[keyIndex].removeRow(0);
						resourceDataTableArray[keyIndex].addRow();
						int rowCount = resourceDataTableArray[keyIndex].getNumberOfRows();
	
						for (int i = 0; i < seconds; i++) {
							resourceDataTableArray[keyIndex].setCell(i, 0, i, i
									+ " sec");
						}
						resourceDataTableArray[keyIndex].setCell(rowCount - 1, 1, resourceValue, Double.toString(resourceValue));
					}
					
					keyIndex++;
				}
				
				CPUPlot.redraw();
				VirtMemPlot.redraw();
				NetSentPlot.redraw();
				NetRecvPlot.redraw();
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
