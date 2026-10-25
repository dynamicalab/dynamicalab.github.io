function updateTruncationLinks() {
  document.querySelectorAll('.home-news-item').forEach(newsItem => {
    const excerpt = newsItem.querySelector('.home-news-excerpt');
    const link = newsItem.querySelector('.home-news-more-details');
    if (!excerpt || !link) return;

    // Temporarily show the link's container check is unnecessary since
    // .news-excerpt's clamp is independent of the link's display state,
    // so scrollHeight/clientHeight stay accurate regardless.
    const isTruncated = excerpt.scrollHeight > excerpt.clientHeight + 1; // +1 guards against subpixel rounding
    link.style.display = isTruncated ? 'inline' : 'none';
  });
}

function debounce(fn, wait) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), wait);
  };
}

document.addEventListener('DOMContentLoaded', updateTruncationLinks);
window.addEventListener('resize', debounce(updateTruncationLinks, 150));