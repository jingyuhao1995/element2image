from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io
import base64
import time

def capture_elements(url, css_selectors, output_dir="screenshots"):
    """批量截取多个CSS选择器对应的所有元素
    
    Args:
        url: 网页URL
        css_selectors: CSS选择器列表，可以是单个选择器字符串或选择器列表
        output_dir: 输出目录，默认为'screenshots'
        
    注意事项：
        1. 确保已安装最新版本的Chrome浏览器
        2. 使用homebrew安装chromedriver：
           brew install chromedriver
        3. 如果遇到"Apple无法验证chromedriver"的问题：
           a. 在终端执行：xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
           b. 或在系统偏好设置 > 安全性与隐私 > 通用中允许chromedriver运行
        4. 确保chromedriver版本与Chrome浏览器版本匹配
    """
    import os
    from datetime import datetime
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 将单个选择器转换为列表
    if isinstance(css_selectors, str):
        css_selectors = [css_selectors]
    
    # 初始化Chrome浏览器
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--force-device-scale-factor=1')
    options.add_argument('--force-color-profile=srgb')
    
    driver = None
    try:
        from selenium.webdriver.chrome.service import Service
        # 使用homebrew安装的chromedriver路径
        service = Service('/opt/homebrew/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        
        # 访问页面并等待加载完成
        driver.get(url)
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)  # 额外等待以确保样式加载完成
        
        # 对每个选择器进行处理
        for selector in css_selectors:
            try:
                # 等待并获取所有匹配的元素
                elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                
                # 为每个元素生成截图
                for index, element in enumerate(elements):
                    try:
                        # 滚动到元素位置并等待
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)  # 等待滚动和样式应用完成
                        
                        # 获取元素的位置和大小
                        location = element.location_once_scrolled_into_view
                        size = element.size
                        
                        # 使用JavaScript获取元素的实际尺寸和位置
                        rect = driver.execute_script("""
                            var rect = arguments[0].getBoundingClientRect();
                            return {
                                top: rect.top,
                                left: rect.left,
                                width: rect.width,
                                height: rect.height
                            };
                        """, element)
                        
                        # 截取整个页面
                        screenshot = driver.get_screenshot_as_png()
                        image = Image.open(io.BytesIO(screenshot))
                        
                        # 计算元素在截图中的坐标（考虑设备像素比）
                        scale = driver.execute_script('return window.devicePixelRatio;')
                        left = int(rect['left'] * scale)
                        top = int(rect['top'] * scale)
                        right = int((rect['left'] + rect['width']) * scale)
                        bottom = int((rect['top'] + rect['height']) * scale)
                        
                        # 裁剪图片
                        element_image = image.crop((left, top, right, bottom))
                        
                        # 生成输出文件名
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        selector_name = selector.replace(".", "").replace("#", "").replace(" ", "_")
                        output_path = os.path.join(
                            output_dir,
                            f"{selector_name}_{index + 1}_{timestamp}.png"
                        )
                        
                        # 保存图片
                        element_image.save(output_path)
                        print(f"成功保存截图到: {output_path}")
                        
                    except Exception as element_error:
                        print(f"处理元素 {selector} #{index + 1} 时发生错误: {str(element_error)}")
                        continue
                        
            except Exception as selector_error:
                print(f"处理选择器 {selector} 时发生错误: {str(selector_error)}")
                continue
                
    except Exception as e:
        print(f"发生错误: {str(e)}")
    
    finally:
        if driver:
            driver.quit()

# 使用示例
if __name__ == "__main__":
    url = "https://tft.op.gg/set/14"  # 替换为你要截图的网页URL
    css_selectors = [
        ".self-stretch",  # 第一个要截图的元素的CSS选择器
    ]
    
    # 批量截取元素
    capture_elements(url, css_selectors, "element_screenshots")