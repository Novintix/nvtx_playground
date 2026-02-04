import streamlit as st
import pandas as pd

def render_analytics_dashboard(financial_data, user_role, query):
    """
    Renders visual analytics if the query pertains to finance and user is authorized.
    """
    finance_keywords = ["trend", "performance", "chart", "graph", "sales", "revenue", "history", "compare", "cost", "margin"]
    update_keywords = ["update", "modify", "change", "revise", "set policy"]
    is_update_query = any(kw in query.lower() for kw in update_keywords)
    
    if any(kw in query.lower() for kw in finance_keywords) and user_role != "Guest" and not is_update_query:
        if financial_data:
            with st.expander("📊 Executive Financial Dash", expanded=True):
                # Handle data parsing
                if isinstance(financial_data, str):
                    try:
                        data = pd.read_json(financial_data)
                    except:
                        st.error("Failed to parse financial data.")
                        return
                else:
                    data = pd.DataFrame(financial_data)
                
                data['date'] = pd.to_datetime(data['date'])
                data = data.sort_values('date')
                
                # Metric Cards
                m1, m2, m3 = st.columns(3)
                total_rev = data['revenue'].sum()
                total_cost = data['cost'].sum()
                avg_discount = data['discount_applied'].mean()
                
                margin_pct = ((total_rev/total_cost)-1)*100 if total_cost else 0
                m1.metric("Total Revenue", f"${total_rev:,.0f}", delta=f"{margin_pct:.1f}% Margin")
                m2.metric("Operating Cost", f"${total_cost:,.0f}")
                m3.metric("Avg Discount", f"{avg_discount:.1f}%")
                
                st.divider()
                
                # Charts
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Revenue & Cost Trend**")
                    st.line_chart(data.groupby('date')[['revenue', 'cost']].sum())
                with col2:
                    st.markdown("**Market Share by Product**")
                    st.bar_chart(data.groupby('product')['revenue'].sum())

                col3, col4 = st.columns(2)
                with col3:
                    st.markdown("**Regional Contribution**")
                    st.bar_chart(data.groupby('region')['revenue'].sum())
                with col4:
                    st.markdown("**Revenue vs. Discount Correlation**")
                    st.area_chart(data.groupby('discount_applied')['revenue'].mean())
                    
                st.info("💡 Charts reflect real-time grounding from the secure MCP Corporate Store.")
